```markdown
# 🛠️ Household Services Platform

A basic Flask-based web application intended to manage household services with role-based dashboards for **Admins**, **Customers**, and **Professionals**.

> ⚠️ **Note:**  
> This project is currently **incomplete**. Development was halted due to migration issues and mismatches between the database schema and implemented functionalities.

---

## 🗂️ Project Structure

├── app.py                         # Main Flask application
├── instance/
│   └── household\_services.db      # SQLite database file
├── static/
│   └── uploads/                   # Uploaded documents (PDFs, etc.)
│       ├── DocScanner\_21\_Oct\_2024\_10-37.pdf
│       ├── SHGC\_SG\_AIPPM.pdf
│       └── TOC\_Experiment.docx.pdf
└── templates/                     # HTML templates (Jinja2)
├── add\_service.html
├── admin\_dashboard.html
├── base.html
├── customer\_dashboard.html
├── home.html
├── login.html
├── professional\_dashboard.html
└── register.html
```

---

## ⚙️ Tech Stack

- **Flask** – Python web framework for routing and handling logic
- **SQLite** – Embedded database for local storage
- **Jinja2** – Template rendering for dynamic HTML
- **HTML/CSS (Bootstrap optional)** – Frontend templates and styling

---

## 👥 User Roles (Planned)

- **Admin**
  - Oversee all users and services
  - Admin dashboard access

- **Customer**
  - Register, log in, and request services
  - View submitted service history

- **Professional**
  - View and manage assigned tasks

---

## 🚧 Project Status

- ⚠️ **Incomplete / Stalled**
- Encountered **migration issues** with the database
- Current **schema does not align** with some implemented features
- Further work is needed to rebuild or refactor the database and logic

---

## ▶️ How to Run (for Testing)

1. **Clone the Repository**

   ```bash
   git clone <repo-url>
   cd <project-dir>
````

2. **Set Up Virtual Environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies** (if any)

   ```bash
   pip install -r requirements.txt
   ```

4. **Run the App**

   ```bash
   python app.py
   ```

   Open [http://localhost:5000](http://localhost:5000) in your browser.

---

## 📁 File Uploads

* User-uploaded files (e.g., PDFs) are stored in the `static/uploads/` directory.
* Ensure the `uploads/` directory has write permissions.

---

## 💬 Final Notes

This project is intended as a **prototype** and is currently under construction. You’re welcome to fork, refactor, and extend it based on your own database design or service logic.

