from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json
import os
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///healthsync.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

# Database Models
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with health data
    health_data = db.relationship('HealthData', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class HealthData(db.Model):
    __tablename__ = 'health_data'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    submission_date = db.Column(db.DateTime, default=datetime.utcnow)
    question_answers = db.Column(db.Text, nullable=False)
    assessment_result = db.Column(db.Text, nullable=False)
    
    def get_answers(self):
        return json.loads(self.question_answers)
    
    def set_answers(self, answers_dict):
        self.question_answers = json.dumps(answers_dict)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Health Assessment Logic
def generate_health_assessment(answers):
    """Generate a health assessment based on user answers"""
    risk_factors = []
    recommendations = []
    risk_level = "Low"
    
    # Family history assessment
    if answers.get('family_history') == 'yes':
        risk_factors.append("family history of chronic diseases")
        risk_level = "Moderate"
    
    # Symptoms assessment
    symptoms = answers.get('symptoms', [])
    if isinstance(symptoms, str):
        symptoms = [symptoms]
    
    serious_symptoms = ['chest_pain', 'shortness_of_breath', 'severe_fatigue']
    if any(symptom in serious_symptoms for symptom in symptoms):
        risk_factors.append("experiencing concerning symptoms")
        risk_level = "High"
        recommendations.append("Consult a healthcare professional immediately")
    
    # Exercise assessment
    exercise = answers.get('exercise_frequency')
    if exercise in ['never', 'rarely']:
        risk_factors.append("insufficient physical activity")
        recommendations.append("Increase physical activity gradually")
        if risk_level == "Low":
            risk_level = "Moderate"
    
    # Chronic condition assessment
    chronic_condition = answers.get('chronic_condition', '').strip()
    if chronic_condition:
        risk_factors.append(f"diagnosed chronic condition: {chronic_condition}")
        risk_level = "High"
        recommendations.append("Continue following your healthcare provider's treatment plan")
    
    # Medication assessment
    medications = answers.get('medications', '').strip()
    if medications:
        recommendations.append("Ensure you're taking medications as prescribed")
    
    # Generate assessment text
    assessment = f"Health Assessment Result:\n\nRisk Level: {risk_level}\n\n"
    
    if risk_factors:
        assessment += f"Risk factors identified: {', '.join(risk_factors)}.\n\n"
    
    if recommendations:
        assessment += f"Recommendations:\n"
        for rec in recommendations:
            assessment += f"• {rec}\n"
        assessment += "\n"
    
    assessment += "This assessment is for informational purposes only and should not replace professional medical advice. Please consult with a healthcare provider for proper diagnosis and treatment."
    
    return assessment

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validation
        if not all([username, email, password, confirm_password]):
            flash('All fields are required.', 'error')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('register.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'error')
            return render_template('register.html')
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
            return render_template('register.html')
        
        # Create new user
        user = User(username=username, email=email)
        user.set_password(password)
        
        try:
            db.session.add(user)
            db.session.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred during registration.', 'error')
            return render_template('register.html')
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            flash('Please enter both username and password.', 'error')
            return render_template('login.html')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Get user's latest health data
    latest_assessment = HealthData.query.filter_by(user_id=current_user.id)\
        .order_by(HealthData.submission_date.desc()).first()
    
    total_assessments = HealthData.query.filter_by(user_id=current_user.id).count()
    
    return render_template('dashboard.html', 
                         latest_assessment=latest_assessment,
                         total_assessments=total_assessments)

@app.route('/health-assessment', methods=['GET', 'POST'])
@login_required
def health_assessment():
    if request.method == 'POST':
        # Collect form data
        answers = {
            'family_history': request.form.get('family_history'),
            'symptoms': request.form.getlist('symptoms'),
            'exercise_frequency': request.form.get('exercise_frequency'),
            'chronic_condition': request.form.get('chronic_condition', ''),
            'medications': request.form.get('medications', '')
        }
        
        # Generate assessment
        assessment_result = generate_health_assessment(answers)
        
        # Save to database
        health_data = HealthData(
            user_id=current_user.id,
            assessment_result=assessment_result
        )
        health_data.set_answers(answers)
        
        try:
            db.session.add(health_data)
            db.session.commit()
            flash('Health assessment completed successfully!', 'success')
            return render_template('assessment_result.html', 
                                 assessment=assessment_result,
                                 answers=answers)
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while saving your assessment.', 'error')
    
    return render_template('health_assessment.html')

@app.route('/my-data')
@login_required
def my_data():
    # Get all user's health data, ordered by most recent
    health_records = HealthData.query.filter_by(user_id=current_user.id)\
        .order_by(HealthData.submission_date.desc()).all()
    
    return render_template('my_data.html', health_records=health_records)

@app.route('/chronic-diseases')
def chronic_diseases():
    diseases_info = {
        'diabetes': {
            'name': 'Diabetes',
            'description': 'A group of diseases that result in high blood glucose levels.',
            'symptoms': ['Excessive thirst', 'Frequent urination', 'Unexplained weight loss', 'Fatigue', 'Blurred vision'],
            'risk_factors': ['Family history', 'Obesity', 'Physical inactivity', 'Age over 45', 'High blood pressure'],
            'prevention': ['Maintain healthy weight', 'Exercise regularly', 'Eat a balanced diet', 'Limit processed foods', 'Regular health screenings'],
            'management': ['Monitor blood sugar levels', 'Take medications as prescribed', 'Follow meal planning', 'Exercise regularly', 'Regular medical checkups']
        },
        'hypertension': {
            'name': 'Hypertension (High Blood Pressure)',
            'description': 'A condition where blood pressure is consistently elevated.',
            'symptoms': ['Often no symptoms', 'Headaches', 'Shortness of breath', 'Nosebleeds', 'Chest pain'],
            'risk_factors': ['Family history', 'Obesity', 'High sodium intake', 'Physical inactivity', 'Smoking', 'Excessive alcohol'],
            'prevention': ['Maintain healthy weight', 'Reduce sodium intake', 'Exercise regularly', 'Limit alcohol', 'Don\'t smoke', 'Manage stress'],
            'management': ['Take medications as prescribed', 'Monitor blood pressure', 'Follow DASH diet', 'Exercise regularly', 'Manage stress']
        },
        'heart_disease': {
            'name': 'Heart Disease',
            'description': 'Various conditions that affect heart function and blood vessels.',
            'symptoms': ['Chest pain', 'Shortness of breath', 'Fatigue', 'Irregular heartbeat', 'Swelling in legs/feet'],
            'risk_factors': ['High cholesterol', 'High blood pressure', 'Diabetes', 'Smoking', 'Family history', 'Obesity'],
            'prevention': ['Eat heart-healthy diet', 'Exercise regularly', 'Maintain healthy weight', 'Don\'t smoke', 'Manage stress', 'Control diabetes and blood pressure'],
            'management': ['Take medications as prescribed', 'Follow cardiac diet', 'Exercise as recommended', 'Monitor symptoms', 'Regular cardiology visits']
        }
    }
    
    return render_template('chronic_diseases.html', diseases=diseases_info)

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

# Initialize database
#@app.before_first_request
#def create_tables():
 #   db.create_all()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)