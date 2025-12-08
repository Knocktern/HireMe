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

