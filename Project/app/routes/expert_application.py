from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, current_app
from extensions import db
from models import User, Skill, InterviewerApplication, InterviewerProfile
from werkzeug.security import generate_password_hash
from datetime import datetime
import json
import traceback

bp = Blueprint('expert_application', __name__)


# =====================================================
# LANDING PAGE - APPLY AS EXPERT INTERVIEWER
# =====================================================
@bp.route('/become-expert-interviewer')
def become_expert():
    """Landing page for expert interviewer application"""
    skills = Skill.query.order_by(Skill.skill_name).all()
    
    # Common industries list
    industries = [
        'Technology', 'Finance & Banking', 'Healthcare', 'E-commerce',
        'Education', 'Manufacturing', 'Telecommunications', 'Media & Entertainment',
        'Real Estate', 'Consulting', 'Automotive', 'Energy', 'Retail',
        'Logistics & Supply Chain', 'Insurance', 'Government', 'Non-Profit'
    ]
    
    return render_template('expert/become_expert.html',
                         skills=skills,
                         industries=industries)


@bp.route('/apply-as-expert', methods=['GET', 'POST'])
def apply_as_expert():
    """Expert interviewer application form"""
    if request.method == 'POST':
        try:
            # Check if email already exists
            email = request.form.get('email', '').strip()
            first_name = request.form.get('first_name', '').strip()
            last_name = request.form.get('last_name', '').strip()
            
            # Validate required fields
            if not email:
                flash('Email is required.', 'error')
                return redirect(url_for('expert_application.apply_as_expert'))
            if not first_name:
                flash('First name is required.', 'error')
                return redirect(url_for('expert_application.apply_as_expert'))
            if not last_name:
                flash('Last name is required.', 'error')
                return redirect(url_for('expert_application.apply_as_expert'))
                
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                flash('This email is already registered. Please login or use a different email.', 'error')
                return redirect(url_for('expert_application.apply_as_expert'))
            
            existing_application = InterviewerApplication.query.filter_by(
                email=email, status='pending'
            ).first()
            if existing_application:
                flash('An application with this email is already pending review.', 'warning')
                return redirect(url_for('expert_application.apply_as_expert'))
            
            # Parse experience years safely
            exp_years_str = request.form.get('experience_years', '0')
            try:
                experience_years = int(exp_years_str) if exp_years_str else 0
            except (ValueError, TypeError):
                experience_years = 0
            
            # Parse hourly rate safely
            hourly_rate_str = request.form.get('hourly_rate', '0')
            try:
                hourly_rate = float(hourly_rate_str) if hourly_rate_str else 0.0
            except (ValueError, TypeError):
                hourly_rate = 0.0
            
            # Create application
            application = InterviewerApplication(
                email=email,
                first_name=first_name,
                last_name=last_name,
                phone=request.form.get('phone', '').strip() or None,
                headline=request.form.get('headline', '').strip() or None,
                bio=request.form.get('bio', '').strip() or None,
                experience_years=experience_years,
                linkedin_url=request.form.get('linkedin_url', '').strip() or None,
                hourly_rate=hourly_rate,
                currency=request.form.get('currency', 'USD') or 'USD'
            )
            
            # Skills (as JSON)
            skill_ids = request.form.getlist('skills')
            skills_data = []
            for skill_id in skill_ids:
                try:
                    skill = Skill.query.get(int(skill_id))
                    if skill:
                        skills_data.append({
                            'id': skill.id,
                            'name': skill.skill_name,
                            'proficiency': 'Expert'
                        })
                except (ValueError, TypeError):
                    continue
            application.skills_json = json.dumps(skills_data)
            
            # Industries (as JSON)
            industries = request.form.getlist('industries')
            application.industries_json = json.dumps(industries)
            
            # Job roles
            job_roles = request.form.get('job_roles', '').split(',')
            job_roles = [r.strip() for r in job_roles if r.strip()]
            
            # CV upload
            cv_file = request.files.get('cv_file')
            if cv_file and cv_file.filename:
                application.cv_content = cv_file.read()
                application.cv_filename = cv_file.filename
                application.cv_mimetype = cv_file.mimetype
            else:
                flash('CV/Resume is required.', 'error')
                return redirect(url_for('expert_application.apply_as_expert'))
            
            # Experience proof upload
            exp_file = request.files.get('experience_proof')
            if exp_file and exp_file.filename:
                application.experience_proof_content = exp_file.read()
                application.experience_proof_filename = exp_file.filename
                application.experience_proof_mimetype = exp_file.mimetype
            
            # Certifications (as JSON)
            cert_names = request.form.getlist('cert_name')
            cert_orgs = request.form.getlist('cert_org')
            cert_urls = request.form.getlist('cert_url')
            
            certifications = []
            for i in range(len(cert_names)):
                if cert_names[i]:
                    certifications.append({
                        'name': cert_names[i],
                        'organization': cert_orgs[i] if i < len(cert_orgs) else '',
                        'url': cert_urls[i] if i < len(cert_urls) else ''
                    })
            application.certifications_json = json.dumps(certifications)
            
            db.session.add(application)
            db.session.commit()
            
            # Notify all admins about new application
            from models import Notification
            admins = User.query.filter_by(user_type='admin', is_active=True).all()
            for admin in admins:
                notification = Notification(
                    user_id=admin.id,
                    title='New Expert Interviewer Application',
                    message=f'{first_name} {last_name} has applied to become an expert interviewer. Review their application.',
                    notification_type='system',
                    action_url=f'/admin/interviewer-applications/{application.id}'
                )
                db.session.add(notification)
            db.session.commit()
            
            flash('Your application has been submitted successfully! We will review it and get back to you soon.', 'success')
            return redirect(url_for('expert_application.application_submitted', app_id=application.id))
            
        except Exception as e:
            db.session.rollback()
            # Log the full error for debugging
            import traceback
            error_details = traceback.format_exc()
            current_app.logger.error(f'Expert application error: {str(e)}')
            current_app.logger.error(error_details)
            # Temporarily show actual error for debugging
            flash(f'Error: {str(e)}', 'error')
            return redirect(url_for('expert_application.apply_as_expert'))
    
    # GET request - show form
    skills = Skill.query.order_by(Skill.skill_name).all()
    industries = [
        'Technology', 'Finance & Banking', 'Healthcare', 'E-commerce',
        'Education', 'Manufacturing', 'Telecommunications', 'Media & Entertainment',
        'Real Estate', 'Consulting', 'Automotive', 'Energy', 'Retail',
        'Logistics & Supply Chain', 'Insurance', 'Government', 'Non-Profit'
    ]
    
    return render_template('expert/apply_form.html',
                         skills=skills,
                         industries=industries)


@bp.route('/application-submitted/<int:app_id>')
def application_submitted(app_id):
    """Confirmation page after application submission"""
    application = InterviewerApplication.query.get_or_404(app_id)
    return render_template('expert/application_submitted.html', application=application)


@bp.route('/check-application-status', methods=['GET', 'POST'])
def check_application_status():
    """Check application status by email"""
    if request.method == 'POST':
        email = request.form.get('email')
        application = InterviewerApplication.query.filter_by(email=email).order_by(
            InterviewerApplication.created_at.desc()
        ).first()
        
        if application:
            return render_template('expert/application_status.html', application=application)
        else:
            flash('No application found with this email address.', 'warning')
    
    return render_template('expert/check_status.html')
