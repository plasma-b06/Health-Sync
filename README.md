HealthSync Web Application
Overview
HealthSync is a web application built with Flask and Bootstrap 5, allowing users to register, log in, complete a health assessment for chronic diseases, view their health data, and access information about chronic diseases. It uses SQLite for data storage and implements secure user authentication and data handling.
Setup Instructions

Install Dependencies:

Ensure Python 3.8+ is installed.
Create a virtual environment: python -m venv venv
Activate the virtual environment:
Windows: venv\Scripts\activate
Unix/Linux: source venv/bin/activate


Install required packages: pip install -r requirements.txt


Set Up the Database:

The application uses SQLite by default (healthsync.db).
The database is automatically created when you run the app for the first time.
