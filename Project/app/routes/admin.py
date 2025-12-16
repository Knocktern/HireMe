from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, send_file
from extensions import db
from models import (
    User, Notification, ActivityLog, JobPosting, JobApplication,
    Company, Skill, CandidateSkill, JobRequiredSkill, CandidateProfile,
    InterviewRoom, InterviewParticipant, InterviewFeedback, InterviewerRecommendation,
    InterviewerApplication, InterviewerProfile, InterviewerSkill, InterviewerIndustry,
    InterviewerCertification, InterviewerJobRole
)
from datetime import datetime, timedelta
from io import BytesIO
from sqlalchemy import func, text, and_, or_
from werkzeug.security import generate_password_hash
import csv
import json

bp = Blueprint('admin', __name__, url_prefix='/admin')

# --- ADMIN DASHBOARD ---
@bp.route('/dashboard')
def admin_dashboard():
    if 'user_id' not in session or session['user_type'] != 'admin':
        return redirect(url_for('auth.login'))
    
    # System statistics
    stats = {
        'total_users': User.query.count(),
        'total_candidates': User.query.filter_by(user_type='candidate').count(),
        'candidates': User.query.filter_by(user_type='candidate').count(),
        'total_employers': User.query.filter_by(user_type='employer').count(),
        'employers': User.query.filter_by(user_type='employer').count(),
        'total_interviewers': User.query.filter_by(user_type='interviewer').count(),
        'interviewers': User.query.filter_by(user_type='interviewer').count(),
        'pending_interviewer_apps': InterviewerApplication.query.filter_by(status='pending').count(),
        'total_jobs': JobPosting.query.count(),
        'active_jobs': JobPosting.query.filter_by(is_active=True).count(),
        'total_applications': JobApplication.query.count(),
        'total_skills': Skill.query.count(),
        'total_companies': Company.query.count(),
        'new_users_today': User.query.filter(func.date(User.created_at) == func.date(datetime.now())).count(),
        'new_applications_today': JobApplication.query.filter(func.date(JobApplication.applied_at) == func.date(datetime.now())).count()
    }
    
    # Recent activity
    recent_activities = ActivityLog.query.order_by(
        ActivityLog.timestamp.desc()
    ).limit(20).all()
    
    # User registration trends (last 30 days)
    thirty_days_ago = datetime.now() - timedelta(days=30)
    daily_registrations = db.session.query(
        func.date(User.created_at).label('date'),
        func.count(User.id).label('count')
    ).filter(
        User.created_at >= thirty_days_ago
    ).group_by(func.date(User.created_at)).all()
    
    return render_template('admin/admin_dashboard.html',
                         stats=stats,
                         recent_activities=recent_activities,
                         daily_registrations=daily_registrations)


