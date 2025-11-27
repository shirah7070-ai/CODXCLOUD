# CodXCloud Library Management System

A comprehensive Library Management System built with Python, Tkinter, TtkBootstrap and MySQL. This application provides a modern GUI for managing books, user accounts, and financial transactions within a library environment.

## Features

*   **User Authentication**: Secure login and registration system for library members.
*   **Password Confidentiality**: Secure password input by covering input with (***).
*   **Book Management**:
    *   Browse and search for books by Title or Author.
    *   View real-time availability status.
    *   Borrow and return books with automated due date tracking.
*   **Wallet & Transactions**:
    *   Integrated digital wallet for every user.
    *   Top-up balance via simulated Credit/Debit Card or QR Code payment.
    *   Transaction history tracking.
    *   Automated late fee calculation and payment system.
*   **Modern UI**: Built with `ttkbootstrap` for a clean, responsive, and theme-aware user interface.
*   **Database Driven**: Robust data persistence using MySQL.

## Prerequisites

Before running the application, ensure you have the following installed:

*   **Python 3.x**: [Download Python](https://www.python.org/downloads/)
*   **MySQL Server**: [Download MySQL](https://dev.mysql.com/downloads/installer/)

### Python Dependencies

Install the required Python packages:

```bash
pip install tkinter
pip install ttkbootstrap
pip install mysql-connector-python
pip install Pillow
```

## Installation & Setup

1.  **Database Configuration**
    *   Ensure your MySQL server is running.
    *   Open `db_setup.py` and check the `DatabaseManager` class `__init__` method to match your MySQL credentials (default: `root`/`admin`).
    
    ```python
    self.host = "localhost"
    self.user = "root"
    self.password = "admin"
    ```

2.  **Initialize Database**
    Run the setup script to create the database (`codxcloud_db`) and populate it with initial data (books and admin user).

    ```bash
    python db_setup.py
    ```

## Usage

1.  **Run the Application**
    Execute the main script to launch the GUI.

    ```bash
    python main.py
    ```
    *(Note: The main script is named `main.py` without an extension. It is a valid Python script.)*

2.  **Login**
    *   **Default Admin User**:
        *   Username: `admin`
        *   Password: `admin123`
    *   Or register a new account via the "Register" button.

3.  **Explore Features**
    *   **Search**: Find books to borrow.
    *   **Borrow/Return**: Manage your loans.
    *   **Profile**: View your borrowed books and due dates.
    *   **Top Up**: Add funds to your wallet to pay for fines or services.
    *   **Transactions**: View and records initial transactions made by users.
    *   **Donate**: Donates funds to services only.

## Project Structure

*   `main.py`: The main entry point for the application (GUI logic).
*   `db_setup.py`: Database connection, schema creation, and initial data seeding.
*   `book_cover/`: Directory containing application assets (images, etc.).

## Troubleshooting

*   **Database Connection Error**: Ensure MySQL is running and the credentials in `db_setup.py` match your local setup.
*   **Missing Modules**: Run `pip install -r requirements.txt` (if available) or install dependencies manually as listed above.
