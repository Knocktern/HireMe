from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, Response
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta
from io import BytesIO
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash

from extensions import db
from models import (
    User, Company, JobPosting, JobApplication, JobRequiredSkill,
    CandidateProfile, CandidateSkill, Skill, MCQExam, MCQQuestion,
    InterviewerRecommendation, ActivityLog, Notification, ApplicationStatusHistory, InterviewRoom,
    InterviewerProfile, InterviewerSkill, InterviewerIndustry, InterviewerAvailability,
    InterviewerReview, InterviewerJobRole
)
from services import log_activity, create_notification
from services.job_matching_service import calculate_job_match_score
from utils.file_utils import allowed_file
from flask import send_file
import json

bp = Blueprint('employer', __name__, url_prefix='/employer')


@bp.route('/company/profile', methods=['GET', 'POST'])
def company_profile():
    """View and edit company profile"""
    if 'user_id' not in session or session['user_type'] != 'employer':
        return redirect(url_for('auth.login'))
    
    user = User.query.get(session['user_id'])
    company = user.company
    
    if not company:
        flash('Company not found. Please contact support.', 'error')
        return redirect(url_for('employer.employer_dashboard'))
    
    if request.method == 'POST':
        try:
            company.company_name = request.form.get('company_name', company.company_name)
            company.industry = request.form.get('industry', '')
            company.company_size = request.form.get('company_size', '')
            company.location = request.form.get('location', '')
            company.description = request.form.get('description', '')
            company.website = request.form.get('website', '')
            
            # Handle logo upload if provided
            if 'logo' in request.files:
                logo_file = request.files['logo']
                if logo_file and logo_file.filename:
                    # Check allowed image extensions
                    allowed_image_ext = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
                    ext = logo_file.filename.rsplit('.', 1)[1].lower() if '.' in logo_file.filename else ''
                    if ext in allowed_image_ext:
                        company.logo = logo_file.read()
                        company.logo_filename = secure_filename(logo_file.filename)
            
            db.session.commit()
            
            log_activity('companies', 'UPDATE', company.id,
                        new_values={'company_name': company.company_name, 'industry': company.industry})
            
            flash('Company profile updated successfully!', 'success')
            return redirect(url_for('employer.company_profile'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating profile: {str(e)}', 'error')
    
    # Industry options
    industries = [
        'Technology', 'Healthcare', 'Finance', 'Education', 'Manufacturing',
        'Retail', 'Consulting', 'Media & Entertainment', 'Telecommunications',
        'Real Estate', 'Transportation', 'Energy', 'Agriculture', 'Hospitality',
        'Legal', 'Non-Profit', 'Government', 'Automotive', 'Aerospace', 'Other'
    ]
    
    return render_template('employer/company_profile.html',
                         user=user,
                         company=company,
                         industries=industries)
