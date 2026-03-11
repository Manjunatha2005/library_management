#  Library Management System

A Python-based **Library Management System** designed to manage books, users, and library operations efficiently using **MySQL database integration**. The system allows administrators and users to perform common library tasks such as adding books, issuing books, returning books, and managing records through a structured menu-driven interface.

##  Features

* 🔐 **Login System** for admin and users
* 📖 **Book Management** – Add, update, delete, and search books
* 👤 **User Management** – Register and manage library users
* 📤 **Issue Books** – Track books issued to users
* 📥 **Return Books** – Update records when books are returned
* 🗄 **MySQL Database Integration** – Persistent data storage
* 📊 **Record Management** – Maintain structured library records
* ⚡ **Menu-Driven Interface** for easy interaction

## 🛠 Technologies Used

* **Python**
* **MySQL**
* **mysql-connector-python**
* **VS Code**

## 📂 Project Structure

```
Library-Management-System
│
├── ProjectLogin.py      # Entry point of the program
├── MainMenu.py          # Main menu interface
├── Admin.py             # Admin operations
├── User.py              # User operations
├── Book.py              # Book management
├── Operations.py        # Issue and return book functions
├── Tables.py            # MySQL database connection & table setup
└── README.md
```

## 🗃 Database

The system uses **MySQL** to store library data such as:

* Books
* Users
* Issued Books
* Returned Books

## ▶ How to Run

1. Install required Python package:

```
pip install mysql-connector-python
```

2. Start MySQL server.

3. Configure database credentials in `Tables.py`.

4. Run the project:

```
python ProjectLogin.py
```

## 🎯 Purpose

This project demonstrates **database integration with Python** and simulates real-world library operations, making it useful for **learning database-driven application development**.

---

💡 Developed as part of a **software development / database practice project**.
