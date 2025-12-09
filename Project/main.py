from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os


app = Flask(__name__)
app.secret_key = 'secret'

# Database connection
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:<use_your_password>@localhost:3306/job_matching_system'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ===== MODELS =====


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    user_type = db.Column(db.Enum('candidate', 'employer', 'admin', 'interviewer', 'manager'), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime)
    
    candidate_profile = db.relationship('CandidateProfile', backref='user', uselist=False)
    company = db.relationship('Company', backref='user', uselist=False)

class CandidateProfile(db.Model):
    __tablename__ = 'candidate_profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    experience_years = db.Column(db.Integer, default=0)
    education_level = db.Column(db.Enum('High School', 'Bachelor', 'Master', 'PhD', 'Other'))
    current_position = db.Column(db.String(255))
    location = db.Column(db.String(255))
    salary_expectation = db.Column(db.Numeric(10, 2))
    cv_file_path = db.Column(db.String(500))
    cv_content = db.Column(db.LargeBinary)
    cv_filename = db.Column(db.String(255))
    cv_mimetype = db.Column(db.String(100))
    summary = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Company(db.Model):
    __tablename__ = 'companies'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    company_name = db.Column(db.String(255), nullable=False)
    industry = db.Column(db.String(100))
    company_size = db.Column(db.Enum('1-10', '11-50', '51-200', '201-500', '500+'))
    location = db.Column(db.String(255))
    description = db.Column(db.Text)
    website = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class JobPosting(db.Model):
    __tablename__ = 'job_postings'
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    requirements = db.Column(db.Text)
    location = db.Column(db.String(255))
    job_type = db.Column(db.Enum('Full-time', 'Part-time', 'Contract', 'Internship'))
    experience_required = db.Column(db.Integer, default=0)
    salary_min = db.Column(db.Numeric(10, 2))
    salary_max = db.Column(db.Numeric(10, 2))
    application_deadline = db.Column(db.Date)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class JobApplication(db.Model):
    __tablename__ = 'job_applications'
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('job_postings.id'), nullable=False)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidate_profiles.id'), nullable=False)
    cover_letter = db.Column(db.Text)
    application_status = db.Column(db.Enum('applied', 'under_review', 'shortlisted', 'interview_scheduled', 'rejected', 'hired'), default='applied')
    exam_score = db.Column(db.Numeric(5, 2))
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    job = db.relationship('JobPosting')
    candidate = db.relationship('CandidateProfile')

class InterviewRoom(db.Model):
    __tablename__ = 'interview_rooms'
    id = db.Column(db.Integer, primary_key=True)
    room_name = db.Column(db.String(255), nullable=False)
    room_code = db.Column(db.String(50), unique=True, nullable=False)
    job_application_id = db.Column(db.Integer, db.ForeignKey('job_applications.id'), nullable=False)
    scheduled_time = db.Column(db.DateTime, nullable=False)
    duration_minutes = db.Column(db.Integer, default=60)
    status = db.Column(db.Enum('scheduled', 'active', 'completed', 'cancelled'), default='scheduled')
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime)
    ended_at = db.Column(db.DateTime)
    
    application = db.relationship('JobApplication', backref='interview_room')
    participants = db.relationship('InterviewParticipant', backref='room', lazy=True)
    feedback = db.relationship('InterviewFeedback', backref='room', lazy=True)


class InterviewParticipant(db.Model):
    __tablename__ = 'interview_participants'
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('interview_rooms.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    role = db.Column(db.Enum('candidate', 'interviewer', 'observer'), nullable=False)
    joined_at = db.Column(db.DateTime)
    left_at = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=False)
    
    user = db.relationship('User', backref='interview_participations')


class InterviewFeedback(db.Model):
    __tablename__ = 'interview_feedback'
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('interview_rooms.id'), nullable=False)
    interviewer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    candidate_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    technical_score = db.Column(db.Integer)
    communication_score = db.Column(db.Integer)
    problem_solving_score = db.Column(db.Integer)
    overall_rating = db.Column(db.Enum('excellent', 'good', 'average', 'poor'))
    feedback_text = db.Column(db.Text)
    recommendation = db.Column(db.Enum('hire', 'maybe', 'reject'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    interviewer = db.relationship('User', foreign_keys=[interviewer_id])
    candidate = db.relationship('User', foreign_keys=[candidate_id])


# ===== ROUTES =====

@app.route('/')
def index():
    """Landing page"""
    if 'user_id' in session:
        user_type = session.get('user_type')
        if user_type == 'candidate':
            return redirect(url_for('candidate_dashboard'))
        elif user_type == 'employer':
            return redirect(url_for('employer_dashboard'))
        elif user_type == 'admin':
            return redirect(url_for('admin_dashboard'))
        elif user_type == 'manager':
            return redirect(url_for('manager_dashboard'))
        elif user_type == 'interviewer':
            return redirect(url_for('interviewer_dashboard'))
    
    return render_template('index.html')



#Sign up feature
@app.route('/register', methods=['GET', 'POST'])
def register():
    """Registration page"""
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user_type = request.form['user_type']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        phone = request.form.get('phone', '')
        
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered', 'error')
            return redirect(url_for('register'))
        
        try:
            password_hash = generate_password_hash(password)
            new_user = User(
                email=email,
                password_hash=password_hash,
                user_type=user_type,
                first_name=first_name,
                last_name=last_name,
                phone=phone
            )
            db.session.add(new_user)
            db.session.flush()
            
            if user_type == 'candidate':
                candidate_profile = CandidateProfile(user_id=new_user.id)
                db.session.add(candidate_profile)
            elif user_type == 'employer':
                company_name = request.form.get('company_name', '')
                company = Company(user_id=new_user.id, company_name=company_name)
                db.session.add(company)
            elif user_type == 'manager':
                # Manager specific setup if needed in future
                pass
            elif user_type == 'interviewer':
                # Interviewer specific setup if needed in future
                pass
            
            db.session.commit()
            
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Registration failed: {str(e)}', 'error')
    
    return render_template('register.html')


#login feature
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = User.query.filter_by(email=email, is_active=True).first()
        
        if user and check_password_hash(user.password_hash, password):
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            session['user_id'] = user.id
            session['user_type'] = user.user_type
            session['user_name'] = f"{user.first_name} {user.last_name}"
            
            if user.user_type == 'candidate':
                return redirect(url_for('candidate_dashboard'))
            elif user.user_type == 'employer':
                return redirect(url_for('employer_dashboard'))
            elif user.user_type == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user.user_type == 'manager':
                return redirect(url_for('manager_dashboard'))
            elif user.user_type == 'interviewer':
                return redirect(url_for('interviewer_dashboard'))
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('login.html')


@app.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    flash('You have been logged out successfully', 'info')
    return redirect(url_for('index'))


# ===== CANDIDATE ROUTES =====

@app.route('/candidate/dashboard')
def candidate_dashboard():
    """Candidate dashboard"""
    if 'user_id' not in session or session['user_type'] != 'candidate':
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    profile = user.candidate_profile
    
    if not profile:
        flash('Please complete your profile first', 'error')
        return redirect(url_for('index'))
    
    # Get recent applications
    applications = list(db.session.query(JobApplication, JobPosting, Company).join(
        JobPosting, JobApplication.job_id == JobPosting.id
    ).join(
        Company, JobPosting.company_id == Company.id
    ).filter(
        JobApplication.candidate_id == profile.id
    ).order_by(JobApplication.applied_at.desc()).all())
    
    # Get upcoming interviews
    upcoming_interviews = list(db.session.query(InterviewRoom, JobApplication, JobPosting, Company).join(
        JobApplication, InterviewRoom.job_application_id == JobApplication.id
    ).join(
        JobPosting, JobApplication.job_id == JobPosting.id
    ).join(
        Company, JobPosting.company_id == Company.id
    ).filter(
        JobApplication.candidate_id == profile.id,
        InterviewRoom.status.in_(['scheduled', 'active']),
        InterviewRoom.scheduled_time >= datetime.utcnow()
    ).order_by(InterviewRoom.scheduled_time.asc()).all())
    
    # Calculate stats
    total_applications = len(applications)
    pending_count = sum(1 for app, _, _ in applications if app.application_status == 'applied')
    shortlisted_count = sum(1 for app, _, _ in applications if app.application_status == 'shortlisted')
    avg_match_score = 75  # Placeholder
    
    # Mock recommendations
    recommendations = []
    
    # Mock exams
    exam_invitations = []
    
    return render_template('candidate_dashboard.html',
                         user=user,
                         profile=profile,
                         applications=applications,
                         upcoming_interviews=upcoming_interviews,
                         total_applications=total_applications,
                         pending_count=pending_count,
                         shortlisted_count=shortlisted_count,
                         avg_match_score=avg_match_score,
                         recommendations=recommendations,
                         exam_invitations=exam_invitations)



# ===== EMPLOYER ROUTES =====

@app.route('/employer/dashboard')
def employer_dashboard():
    """Employer dashboard"""
    if 'user_id' not in session or session['user_type'] != 'employer':
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    company = user.company
    
    if not company:
        flash('Please complete your company profile first', 'error')
        return redirect(url_for('index'))
    
    # Get job postings
    job_postings = list(db.session.query(JobPosting).filter_by(company_id=company.id).all())
    active_jobs = sum(1 for job in job_postings if job.is_active)
    
    # Get applications
    applications = list(db.session.query(JobApplication, JobPosting, CandidateProfile, User).join(
        JobPosting, JobApplication.job_id == JobPosting.id
    ).join(
        CandidateProfile, JobApplication.candidate_id == CandidateProfile.id
    ).join(
        User, CandidateProfile.user_id == User.id
    ).filter(
        JobPosting.company_id == company.id
    ).order_by(JobApplication.applied_at.desc()).all())
    
    total_applications = len(applications)
    
    # Mock analytics
    analytics = {
        'total_applications': total_applications,
        'status_counts': {
            'applied': sum(1 for app, _, _, _ in applications if app.application_status == 'applied'),
            'under_review': sum(1 for app, _, _, _ in applications if app.application_status == 'under_review'),
            'shortlisted': sum(1 for app, _, _, _ in applications if app.application_status == 'shortlisted'),
            'rejected': sum(1 for app, _, _, _ in applications if app.application_status == 'rejected'),
        },
        'top_jobs': [(job.title, len([a for a, j, _, _ in applications if j.id == job.id])) for job in job_postings[:5]]
    }
    
    return render_template('employer_dashboard.html',
                         user=user,
                         company=company,
                         job_postings=[(job, sum(1 for a, j, _, _ in applications if j.id == job.id)) for job in job_postings],
                         applications=applications,
                         active_jobs=active_jobs,
                         total_applications=total_applications,
                         analytics=analytics)
    
    
    

# ===== INTERVIEWER ROUTES =====

@app.route('/interviewer/dashboard')
def interviewer_dashboard():
    """Interviewer dashboard"""
    if 'user_id' not in session or session['user_type'] != 'interviewer':
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    
    # Get upcoming interviews for this interviewer
    upcoming_interviews = list(db.session.query(InterviewRoom, JobApplication, JobPosting, Company).join(
        JobApplication, InterviewRoom.job_application_id == JobApplication.id
    ).join(
        JobPosting, JobApplication.job_id == JobPosting.id
    ).join(
        Company, JobPosting.company_id == Company.id
    ).join(
        InterviewParticipant, InterviewRoom.id == InterviewParticipant.room_id
    ).filter(
        InterviewParticipant.user_id == session['user_id'],
        InterviewRoom.status.in_(['scheduled', 'active']),
        InterviewRoom.scheduled_time >= datetime.utcnow()
    ).order_by(InterviewRoom.scheduled_time.asc()).all())
    
    # Get completed interviews
    completed_interviews = list(db.session.query(InterviewRoom, JobApplication, JobPosting, Company).join(
        JobApplication, InterviewRoom.job_application_id == JobApplication.id
    ).join(
        JobPosting, JobApplication.job_id == JobPosting.id
    ).join(
        Company, JobPosting.company_id == Company.id
    ).join(
        InterviewParticipant, InterviewRoom.id == InterviewParticipant.room_id
    ).filter(
        InterviewParticipant.user_id == session['user_id'],
        InterviewRoom.status == 'completed'
    ).order_by(InterviewRoom.ended_at.desc()).limit(10).all())
    
    return render_template('interviewer_dashboard.html',
                         user=user,
                         upcoming_interviews=upcoming_interviews,
                         completed_interviews=completed_interviews,
                         now=datetime.utcnow())


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)