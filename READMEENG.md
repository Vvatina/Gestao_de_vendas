# EN – Makeup Management System

Status: Completed (improvements pending commit)

Desktop application built in Python, using Tkinter and SQLite, designed to manage clients, products, employees, and orders.

## Features:

User login (admin and employees)

Client management

Product management (with stock control)

Employee management (Admin only)

Order creation

Order details and consultation

Fast search in all lists

## Technologies

Python 3

Tkinter (GUI)

SQLite3 (local database)

Pillow / PIL (images)

hashlib (password hashing)

## Installation
### Install required dependencies:
pip install pillow

### Make sure the icons/ folder exists with the following images:
icons/
  logo.png
  clientes.png
  produtos.png
  funcionarios.png
  encomendas.png
  logout.png

### Run the application:
python gestao_de_maquilhagem.py

Initial Login

The system automatically creates an administrator account: Username: admin Password: admin123

## Notes:

The database file maquilhagem.db is created automatically.

Only the Admin user can remove employees, products, and clients.

Stock quantities update automatically when creating or deleting orders.
