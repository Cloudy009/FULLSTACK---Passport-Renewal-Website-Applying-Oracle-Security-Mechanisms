🛂 Passport Renewal Website – Applying Oracle Security Mechanisms

## 🔒 Introduction
This website is developed to support online passport renewal while applying robust Oracle security mechanisms to ensure the safety of personal data and processing workflows. The project addresses real-world administrative challenges such as complex procedures, lack of transparency, and weak security.

## 🎯 Objectives
- Build an online passport management and renewal system
- Integrate Oracle security features: Trigger, Synonym, RBAC, Column Masking, etc.
- Role-based access control (XT, XD, LT, GS roles)
- User-friendly interface suitable for citizens
- Support the trend of digital transformation in public administration

## 🏗️ Architecture & Access Control
📌 Workflow:
- Citizen submits renewal request
- Verification Department (XT): checks residency information
- Approval Department (XD): approves or rejects requests
- Storage Department (LT): updates results
- Monitoring Department (GS): oversees the entire process

## 🧑‍💼 Role-based Access:
- XT: can only view information in their assigned area
- XD: can only see form data, no direct DB access
- LT: can update status, no access to personal details
- GS: monitors all processing statuses

## 🛡️ Implemented Security Mechanisms
Oracle Feature          Practical Application in System
Trigger	                Enforces request limits, status checks, logging
Synonym	                Hides real schema when accessing data tables
RBAC	                Clear role-based permissions to prevent unauthorized access
Column Masking	        Masks sensitive columns depending on user role
Audit Log               (Trigger)	Records history of request status changes

## 🖼️ Interface & Demo
- Citizen: submits renewal requests
- User_XT: verifies residency information
- User_XD: approves or rejects requests
- User_LT: archives approved information
- User_GS: monitors the entire process

All actions are securely controlled: state verification before approval, no operation if the workflow is invalid.

## 💻 Tech Stack – Technologies Used
This project integrates a variety of technologies to deliver a secure, functional, and user-friendly system:

🔙 Backend
- Django (Python): Handles routing, form processing, session management
- Django ORM: Simplifies database interactions
- Oracle Database (ORCLPDB): Enterprise-grade database with advanced security features

🛡️ Oracle Security Mechanisms
- Trigger: Validates business logic, logs actions
- Synonym: Protects schema by hiding real table names
- RBAC: Role-based restrictions for each department (XT, XD, LT, GS)
- Column Masking: Hides sensitive fields depending on user roles
- Audit Logging: Tracks all critical changes in request workflows

🔐 Authentication & Authorization
- Google OAuth 2.0 and GitHub OAuth: Enables third-party login
- Custom Role Checks: Prevents unauthorized actions in the process

📧 Email Notification
Gmail SMTP: Sends status updates and user notifications

🌐 Frontend
- HTML/CSS/JS: Basic Django templates
- Bootstrap (if used): Improves layout and form appearance

## ⚙️ Infrastructure
- Oracle Instant Client: Required for Python-Oracle connection
- Environment Variables (.env): Stores secure credentials and config

-----------------------------------------------------------------------------------------------

## ⚙️ Setup Instructions
1. Create a virtual environment:
Open Terminal or PowerShell, navigate to your project folder, and run:
python -m venv venv

2. Activate the virtual environment:
+ Trên Windows:     .\venv\Scripts\activate
+ Trên macOS/Linux: source venv/bin/activate

3. Install required libraries:
pip install -r requirements.txt


4. Configure Oracle Instant Client:
- Download and install Oracle Instant Client (matching ORACLE_CLIENT_PATH in your environment variables)
- Ensure Oracle DB service (e.g. ORCLPDB) is running and accessible
- Set your Oracle credentials (ORACLE_DB_USER, ORACLE_DB_PASSWORD) in your .env or environment variables

5. Configure Django environment variables:
Set environment variables for Oracle DB, OAuth (Google/GitHub), email SMTP, etc. as shown below:
SECRET_KEY=your-django-secret-key
DEBUG=True

ORACLE_CLIENT_PATH=path-to-instantclient
ORACLE_DB_NAME=ORCLPDB
ORACLE_DB_USER=your-oracle-user
ORACLE_DB_PASSWORD=your-oracle-password

SOCIAL_AUTH_GOOGLE_OAUTH2_KEY=your-google-client-id
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET=your-google-client-secret
SOCIAL_AUTH_GOOGLE_OAUTH2_REDIRECT_URI=http://127.0.0.1:8000/social-auth/complete/google-oauth2/

SOCIAL_AUTH_GITHUB_KEY=your-github-client-id
SOCIAL_AUTH_GITHUB_SECRET=your-github-client-secret
SOCIAL_AUTH_GITHUB_REDIRECT_URI=http://127.0.0.1:8000/social-auth/complete/github/

EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-email-password
DEFAULT_FROM_EMAIL=your-email@gmail.com
DEFAULT_TO_EMAIL=your-email@gmail.com

6. Run Django migrations:
python manage.py makemigrations
python manage.py migrate

7. Create an admin user:
python manage.py createsuperuser

8. Run the development server:
python manage.py runserver
"# FULLSTACK---Passport-Renewal-Website-Applying-Oracle-Security-Mechanisms" 
