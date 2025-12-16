from flask import Blueprint, render_template, session, redirect, url_for
from sqlalchemy import and_, or_
from extensions import db
from models import User, JobPosting, Company, CandidateProfile, JobApplication

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    # If user is logged in, redirect to their appropriate dashboard
    if 'user_id' in session:
        user_type = session.get('user_type')
        if user_type == 'candidate':
            return redirect(url_for('candidate.candidate_dashboard'))
        elif user_type == 'employer':
            return redirect(url_for('employer.employer_dashboard'))
        elif user_type == 'admin':
            return redirect(url_for('admin.admin_dashboard'))
        elif user_type == 'manager':
            return redirect(url_for('manager.manager_dashboard'))
        elif user_type == 'interviewer':
            return redirect(url_for('interviewer.interviewer_dashboard'))
    
    # For non-logged-in users, show the main landing page
    total_jobs = JobPosting.query.filter_by(is_active=True).count()
    total_companies = Company.query.count()
    total_candidates = CandidateProfile.query.count()
    total_applications = JobApplication.query.count()
    
    recent_jobs = db.session.query(JobPosting, Company).join(Company).filter(
        JobPosting.is_active == True
    ).order_by(JobPosting.created_at.desc()).limit(6).all()
    
    return render_template('index.html',
                          total_jobs=total_jobs,
                          total_companies=total_companies,
                          total_candidates=total_candidates,
                          total_applications=total_applications,
                          recent_jobs=recent_jobs)
