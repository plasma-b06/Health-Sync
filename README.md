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


Run the Application:

Run the Flask app: python app.py
Access the app at http://localhost:5000 in your browser.



Project Structure

app.py: Main Flask application with routes, database setup, and health assessment logic.
templates/: HTML templates for all pages (index, register, login, health assessment, my data, chronic diseases).
requirements.txt: Python dependencies.
healthsync.db: SQLite database (auto-generated).

Extending the Health Assessment
To add more questions or rules to the health assessment:

Update the HealthAssessmentForm class in app.py with new fields.
Modify the generate_assessment function to include new rules based on the added fields.
Update the health_assessment.html template to display the new fields.

Notes

The application uses Flask-WTF for CSRF protection and form validation.
Passwords are hashed using Werkzeug's generate_password_hash.
The health assessment logic is simple and rule-based; it can be extended with more complex rules or machine learning models.
Bootstrap 5 CDN is used for responsive styling.
Ensure environment variables are used for sensitive data (e.g., SECRET_KEY) in production.

Testing

Test registration and login to ensure user authentication works.
Submit the health assessment form and verify data storage in the my-data page.
Check the chronic diseases page for responsive accordion behavior.

Verify that protected routes (/health-assessment, /my-data) redirect unauthenticated users to the login page.
