from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.utils import secure_filename
from functools import wraps
from flask_migrate import Migrate
from datetime import datetime, timezone

import os

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///household_services.db'
db = SQLAlchemy(app)
migrate = Migrate(app, db)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
app.app_context().push()

#Admin Credential
# Single Admin Credentials (Superuser)
SUPER_ADMIN = {
    'username': 'reshav',
    'password': 'reshav123'  # Change this to a more secure password
}


# --------------------
# DATABASE MODELS
# --------------------

# User Model with roles (Admin, Customer, Professional)
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    is_blocked = db.Column(db.Boolean, default=False)  # New field for blocking users
    # # Define the relationship with cascade
    professional = db.relationship(
        'ServiceProfessional',
        cascade="all, delete-orphan",
        lazy=True
    )   
   
class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    address = db.Column(db.String(200), nullable=False)

class ServiceProfessional(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    service_type = db.Column(db.String(50), nullable=False)
    experience = db.Column(db.String(100), nullable=False)
    is_approved = db.Column(db.Boolean, default=False)
    resume_path = db.Column(db.String(200), nullable=True)  # New field for resume upload

    # Define the relationship to the User table
    user = db.relationship('User', lazy=True)

class Service(db.Model):
    id = db.Column(db.Integer,primarykey=True)
    name = db.Column(db.String(50), nullable=False)
    base_price = db.Column(db.Float, nullable=False)
    time_required = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    is_approved = db.Column(db.Boolean, default=False) 
    admin_service_id=db.Column(db.Integer,db.ForeignKey("service.id",name='fk_service_id'),nullable=False)
    
class ServiceRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
     # Foreign Key to Service model
    service_id = db.Column(db.Integer, db.ForeignKey('service.id', name='fk_service_id'), nullable=False)
    service_status = db.Column(db.String(20), default='Requested')  # Status: Requested, In Progress, Completed
    # Foreign Key to User (customer) model
    customer_id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_customer_id'), nullable=False)
    status = db.Column(db.String(20), default='Requested')  # Status: Requested, In Progress, Completed
    date_of_request = db.Column(db.DateTime, nullable=False, default=datetime.now())

    # Relationships
    customer = db.relationship('User', backref='service_requests', lazy=True)  # Define the reverse relationship


# --------------------
# LOGIN MANAGER
# --------------------

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --------------------
# ROUTES
# --------------------

# Home Route
@app.route('/')
def home():
    return render_template('home.html')

# User Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if logging in as admin
        if username == SUPER_ADMIN['username'] and password == SUPER_ADMIN['password']:
            session['admin_logged_in'] = True  # Set only after admin credentials are verified
            flash('Logged in as admin!', 'success')
            return redirect(url_for('admin_dashboard'))

        # Handle regular user login
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            login_user(user)
            flash('Logged in successfully!', 'success')
            if user.role == 'Customer':
                return redirect(url_for('customer_dashboard'))
            elif user.role == 'Professional':
                return redirect(url_for('professional_dashboard'))
        else:
            flash('Invalid credentials', 'error')
    return render_template('login.html')

# User Registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']

        # Prevent admin registration
        if role == 'Admin':
            flash('Cannot register as admin.', 'error')
            return redirect(url_for('register'))
        
        #prevent duplicacy name registration
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return redirect(url_for('register'))

        # Normal registration process
        new_user = User(username=username, password=password, role=role)
        db.session.add(new_user)
        db.session.commit()

        if role == 'Customer':
            address = request.form.get('address')
            customer = Customer(user_id=new_user.id, address=address)
            db.session.add(customer)
        elif role == 'Professional':
            service_type = request.form['service_type']
            experience = request.form['experience']
            resume_file = request.files['resume']
            
            if resume_file and resume_file.filename:
                filename = secure_filename(resume_file.filename)
                resume_path = f"uploads/{filename}"
                full_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                resume_file.save(full_path)
                professional = ServiceProfessional(
                    user_id=new_user.id,
                    service_type=service_type,
                    experience=experience,
                    resume_path=resume_path
                )
                db.session.add(professional)


        db.session.commit()
        flash('Registration successful. Please login.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

# Approve/Reject Professionals
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            flash('You must be logged in as an admin to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# admin_dashboard
@app.route('/admin/dashboard', methods=['GET', 'POST'])
@admin_required
def admin_dashboard():
    # Fetch all users
    users = User.query.filter(User.role != 'Admin').all()

    # Filter users by role (if requested)
    filter_role = request.form.get('filter_role')
    if filter_role:
        users = User.query.filter(User.role == filter_role).all()

    # Fetch all service professionals and services
    professionals = ServiceProfessional.query.all()
    services = Service.query.all()

    return render_template(
        'admin_dashboard.html',
        users=users,
        professionals=professionals,
        services=services
    )

#approve_professional
@app.route('/admin/approve_professional/<int:professional_id>')
@admin_required
def approve_professional(professional_id):
    print(f"Before approval, session['admin_logged_in']: {session.get('admin_logged_in')}")  # Debug

    if not session.get('admin_logged_in'):
        flash('You must be logged in as an admin to perform this action.', 'error')
        return redirect(url_for('login'))

    professional = ServiceProfessional.query.get(professional_id)
    if professional:
        professional.is_approved = True
        db.session.commit()
        flash('Service Professional approved successfully!', 'success')
    else:
        flash('Service Professional not found.', 'error')

    print(f"After approval, session['admin_logged_in']: {session.get('admin_logged_in')}")  # Debug
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/logout')
def admin_logout():
    # Clear session for admin
    session.pop('admin_logged_in', None)
    flash('Admin logged out.', 'info')
    return redirect(url_for('login'))



# Add a new Service
@app.route('/admin/add_service', methods=['GET', 'POST'])
@admin_required
def add_service():
    if request.method == 'POST':
        name = request.form['name']
        base_price = request.form['base_price']
        time_required = request.form['time_required']
        description = request.form['description']

        service = Service(name=name, base_price=base_price, 
        time_required=time_required, 
        description=description)
        db.session.add(service)
        db.session.commit()

        flash('Service added successfully', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('add_service.html')

#to delete created service
@app.route('/admin/delete_service/<int:service_id>', methods=['POST'])
@admin_required
def delete_service(service_id):
    service = Service.query.get(service_id)
    if service:
        db.session.delete(service)
        db.session.commit()
        flash(f'Service "{service.name}" deleted successfully!', 'success')
    else:
        flash('Service not found.', 'error')

    return redirect(url_for('admin_dashboard'))


#approving service
@app.route('/admin/approve_service/<int:service_id>')
@admin_required
def approve_service(service_id):
    service = Service.query.get(service_id)
    if service:
        service.is_approved = True  # Mark service as approved
        db.session.commit()
        flash('Service approved successfully!', 'success')
    else:
        flash('Service not found.', 'error')
    return redirect(url_for('admin_dashboard'))


# Customer Dashboard
@app.route('/customer/dashboard', methods=['GET', 'POST'])
@login_required
def customer_dashboard():
    if current_user.role != 'Customer':
        return redirect(url_for('home'))

    # Fetch all approved services, now linked through ServiceProfessional relationship
    services = (
        db.session.query(Service)
        # .join(ServiceProfessional)  # Join to get services linked to approved professionals
        .filter(ServiceProfessional.is_approved == True)  # Filter for approved professionals only
        .all()
    )

    # Convert services to a dictionary for easier lookup by service_id
    services_dict = {service.id: service for service in services}

    # Fetch all service requests made by the customer
    service_requests = ServiceRequest.query.filter_by(customer_id=current_user.id).all()

    # Build a dictionary to track the status of each service request
    request_status = {request.service_id: request.service_status for request in service_requests}

    return render_template('customer_dashboard.html', services=services_dict, request_status=request_status)



# Professional Dashboard
@app.route('/professional/dashboard')
@login_required
def professional_dashboard():
    if current_user.role != 'Professional':
        return redirect(url_for('home'))

    # Fetch professional details linked to the logged-in user
    professional = ServiceProfessional.query.filter_by(user_id=current_user.id).first()

    return render_template('professional_dashboard.html', professional=professional)

# Service Requests
@app.route('/customer/request_service', methods=['POST'])
@login_required
def request_service():
    if current_user.role != 'Customer':
        return redirect(url_for('home'))

    # Retrieve professional_id from the form
    professional_id = request.form.get('professional_id')

    if not professional_id:
        flash('Professional ID is missing.', 'error')
        return redirect(url_for('customer_dashboard'))

    # Handle the service request creation logic here
    professional = ServiceProfessional.query.get(professional_id)
    if not professional:
        flash('Professional not found.', 'error')
        return redirect(url_for('customer_dashboard'))

    # Check if a service request already exists for this professional
    existing_request = ServiceRequest.query.filter_by(
        customer_id=current_user.id,
        service_id=professional.id,
        service_status='Requested'
    ).first()

    if existing_request:
        flash('You already have a pending service request with this professional.', 'error')
        return redirect(url_for('customer_dashboard'))

    # Create a new service request
    service_request = ServiceRequest(
        service_id=professional.id,  # Assuming professional.id is the service id here
        customer_id=current_user.id,
        service_status='Requested',
        date_of_request=datetime.now()
    )
    db.session.add(service_request)
    db.session.commit()

    flash('Service requested successfully!', 'success')
    return redirect(url_for('customer_dashboard'))

#delete request
@app.route('/customer/delete_request/<int:request_id>', methods=['POST'])
@login_required
def delete_request(request_id):
    if current_user.role != 'Customer':
        return redirect(url_for('home'))

    service_request = ServiceRequest.query.get(request_id)
    if service_request and service_request.customer_id == current_user.id:
        db.session.delete(service_request)
        db.session.commit()
        flash('Your service request has been canceled.', 'success')
    else:
        flash('Service request not found or not authorized.', 'error')

    return redirect(url_for('customer_dashboard'))


#block/unblock user
@app.route('/admin/block_user/<int:user_id>')
@admin_required
def block_user(user_id):
    user = User.query.get(user_id)
    if user:
        user.is_blocked = True
        db.session.commit()
        flash(f'User {user.username} blocked successfully!', 'success')
    else:
        flash('User not found.', 'error')

    return redirect(url_for('admin_dashboard'))


@app.route('/admin/unblock_user/<int:user_id>')
@admin_required
def unblock_user(user_id):
    user = User.query.get(user_id)
    if user:
        user.is_blocked = False
        db.session.commit()
        flash(f'User {user.username} unblocked successfully!', 'success')
    else:
        flash('User not found.', 'error')

    return redirect(url_for('admin_dashboard'))


#delete_user
@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
@admin_required
def delete_user(user_id):
    user = User.query.get(user_id)
    if user:
        # Prevent deleting admins
        if user.role == 'Admin':
            flash('Cannot delete another admin.', 'error')
        else:
            db.session.delete(user)
            db.session.commit()
            flash(f'User {user.username} deleted successfully!', 'success')
    else:
        flash('User not found.', 'error')

    return redirect(url_for('admin_dashboard'))



#logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()  # Ensure session data is removed
    return redirect(url_for('home'))  # Redirect to the login page

# --------------------
# MAIN
# --------------------

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
