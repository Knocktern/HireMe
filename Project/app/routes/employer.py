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
@bp.route('/company/logo')
def company_logo():
    """Serve the company logo for logged-in employer"""
    if 'user_id' not in session or session['user_type'] != 'employer':
        return redirect(url_for('auth.login'))
    
    user = User.query.get(session['user_id'])
    company = user.company
    
    if company and company.logo:
        return send_file(
            BytesIO(company.logo),
            mimetype='image/png',
            download_name=company.logo_filename or 'logo.png'
        )
    
    # Return a placeholder or 404
    return '', 404


@bp.route('/company/<int:company_id>/logo')
def get_company_logo(company_id):
    """Serve company logo by company ID (public)"""
    company = Company.query.get(company_id)
    
    if company and company.logo:
        return send_file(
            BytesIO(company.logo),
            mimetype='image/png',
            download_name=company.logo_filename or 'logo.png'
        )
    
    # Return empty for no logo
    return '', 404


def get_employer_analytics(company_id):
    """Get analytics data for employer dashboard"""
    # Total applications this month
    current_month = datetime.now().replace(day=1)
    total_applications = db.session.query(JobApplication).join(JobPosting).filter(
        JobPosting.company_id == company_id,
        JobApplication.applied_at >= current_month
    ).count()
    
    # Applications by status
    status_counts = db.session.query(
        JobApplication.application_status,
        func.count(JobApplication.id)
    ).join(JobPosting).filter(
        JobPosting.company_id == company_id
    ).group_by(JobApplication.application_status).all()
    
    # Top performing jobs (by application count)
    top_jobs = db.session.query(
        JobPosting.title,
        func.count(JobApplication.id).label('app_count')
    ).outerjoin(JobApplication).filter(
        JobPosting.company_id == company_id
    ).group_by(JobPosting.id).order_by(func.count(JobApplication.id).desc()).limit(5).all()
    
    return {
        'total_applications': total_applications,
        'status_counts': dict(status_counts),
        'top_jobs': top_jobs
    }


@bp.route('/dashboard')
def employer_dashboard():
    if 'user_id' not in session or session['user_type'] != 'employer':
        return redirect(url_for('auth.login'))
    
    user = User.query.get(session['user_id'])
    company = user.company
    
    # Get job postings with application counts
    job_postings = db.session.query(
        JobPosting,
        func.count(JobApplication.id).label('application_count')
    ).outerjoin(JobApplication).filter(
        JobPosting.company_id == company.id
    ).group_by(JobPosting.id).order_by(JobPosting.created_at.desc()).all()
    
    # Get recent applications
    applications = db.session.query(JobApplication, JobPosting, CandidateProfile, User).join(
        JobPosting, JobApplication.job_id == JobPosting.id
    ).join(
        CandidateProfile, JobApplication.candidate_id == CandidateProfile.id
    ).join(
        User, CandidateProfile.user_id == User.id
    ).filter(
        JobPosting.company_id == company.id
    ).order_by(JobApplication.applied_at.desc()).limit(10).all()
    
    # Get notifications
    notifications = Notification.query.filter_by(
        user_id=session['user_id'], is_read=False
    ).order_by(Notification.created_at.desc()).limit(5).all()
    
    # Get analytics data
    analytics = get_employer_analytics(company.id)
    
    # Calculate additional dashboard metrics
    active_jobs_count = db.session.query(JobPosting).filter(
        JobPosting.company_id == company.id,
        JobPosting.is_active == True
    ).count()
    
    # Get new applications (this week)
    one_week_ago = datetime.now() - timedelta(days=7)
    new_applications = db.session.query(JobApplication).join(JobPosting).filter(
        JobPosting.company_id == company.id,
        JobApplication.applied_at >= one_week_ago
    ).count()
    
    # Get scheduled interviews
    scheduled_interviews = db.session.query(InterviewRoom).join(
        JobApplication, InterviewRoom.job_application_id == JobApplication.id
    ).join(
        JobPosting, JobApplication.job_id == JobPosting.id
    ).filter(
        JobPosting.company_id == company.id,
        InterviewRoom.status == 'scheduled',
        InterviewRoom.scheduled_time >= datetime.now()
    ).count()
    
    # Get active exams
    active_exams = db.session.query(MCQExam).join(JobPosting).filter(
        JobPosting.company_id == company.id,
        MCQExam.is_active == True
    ).count()
    
    return render_template('employer/employer_dashboard.html',
                         user=user,
                         company=company,
                         job_postings=job_postings,
                         applications=applications,
                         notifications=notifications,
                         analytics=analytics,
                         active_jobs_count=active_jobs_count,
                         new_applications=new_applications,
                         scheduled_interviews=scheduled_interviews,
                         active_exams=active_exams)


@bp.route('/jobs')
def employer_jobs():
    if 'user_id' not in session or session['user_type'] != 'employer':
        return redirect(url_for('auth.login'))
    
    user = User.query.get(session['user_id'])
    company = user.company
    
    job_postings = db.session.query(
        JobPosting,
        func.count(JobApplication.id).label('application_count')
    ).outerjoin(JobApplication).filter(
        JobPosting.company_id == company.id
    ).group_by(JobPosting.id).order_by(JobPosting.created_at.desc()).all()
    
    return render_template('employer/employer_jobs.html',
                         job_postings=job_postings,
                         user=user,
                         company=company)

@bp.route('/job/create', methods=['GET', 'POST'])
def create_job():
    if 'user_id' not in session or session['user_type'] != 'employer':
        return redirect(url_for('auth.login'))
    
    user = User.query.get(session['user_id'])
    company = user.company
    
    if request.method == 'POST':
        try:
            # Create new job posting
            job = JobPosting(
                company_id=company.id,
                title=request.form['title'],
                description=request.form['description'],
                requirements=request.form.get('requirements', ''),
                location=request.form.get('location', ''),
                job_type=request.form.get('job_type', 'Full-time'),
                experience_required=int(request.form.get('experience_required', 0)),
                salary_min=float(request.form.get('salary_min')) if request.form.get('salary_min') else None,
                salary_max=float(request.form.get('salary_max')) if request.form.get('salary_max') else None,
                is_active=True
            )
            
            db.session.add(job)
            db.session.flush()  # Get job.id
            
            # Add selected skills
            skill_ids = request.form.getlist('skills')
            for skill_id in skill_ids:
                try:
                    job_skill = JobRequiredSkill(
                        job_id=job.id,
                        skill_id=int(skill_id),
                        importance='Required'
                    )
                    db.session.add(job_skill)
                except (ValueError, TypeError):
                    continue
            
            db.session.commit()
            
            flash('Job posting created successfully!', 'success')
            return redirect(url_for('employer.employer_jobs'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating job posting: {str(e)}', 'error')
    
    # Get all skills for the form
    skills = Skill.query.order_by(Skill.skill_name).all()
    
    return render_template('employer/create_job.html', user=user, company=company, skills=skills)


@bp.route('/job/<int:job_id>/exam', methods=['GET', 'POST'])
def manage_job_exam(job_id):
    if 'user_id' not in session or session['user_type'] != 'employer':
        return redirect(url_for('auth.login'))
    
    user = User.query.get(session['user_id'])
    company = user.company
    
    # Verify job belongs to this employer
    job = JobPosting.query.filter_by(id=job_id, company_id=company.id).first()
    if not job:
        flash('Job not found.', 'error')
        return redirect(url_for('employer.employer_dashboard'))
    
    # Get existing exam
    exam = MCQExam.query.filter_by(job_id=job_id).first()
    
    if request.method == 'POST':
        if not exam:
            # Create new exam
            exam = MCQExam(
                job_id=job_id,
                exam_title=request.form.get('exam_title'),
                description=request.form.get('description'),
                duration_minutes=int(request.form.get('duration_minutes', 60)),
                passing_score=float(request.form.get('passing_score', 60.0))
            )
            db.session.add(exam)
        else:
            # Update existing exam
            exam.exam_title = request.form.get('exam_title')
            exam.description = request.form.get('description')
            exam.duration_minutes = int(request.form.get('duration_minutes', 60))
            exam.passing_score = float(request.form.get('passing_score', 60.0))
        
        db.session.commit()
        flash('Exam details saved successfully!', 'success')
        return redirect(url_for('employer.manage_exam_questions', exam_id=exam.id))
    
    return render_template('exam/manage_job_exam.html', job=job, exam=exam)


@bp.route('/exam/<int:exam_id>/questions')
def manage_exam_questions(exam_id):
    if 'user_id' not in session or session['user_type'] != 'employer':
        return redirect(url_for('auth.login'))
    
    user = User.query.get(session['user_id'])
    company = user.company
    
    # Verify exam belongs to this employer
    exam = db.session.query(MCQExam).join(JobPosting).filter(
        MCQExam.id == exam_id,
        JobPosting.company_id == company.id
    ).first()
    
    if not exam:
        flash('Exam not found.', 'error')
        return redirect(url_for('employer.employer_dashboard'))
    
    questions = MCQQuestion.query.filter_by(exam_id=exam_id).all()
    return render_template('exam/manage_exam_questions.html', exam=exam, questions=questions)


@bp.route('/exam/<int:exam_id>/add_question', methods=['GET', 'POST'])
def add_exam_question(exam_id):
    if 'user_id' not in session or session['user_type'] != 'employer':
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        question = MCQQuestion(
            exam_id=exam_id,
            question_text=request.form.get('question_text'),
            option_a=request.form.get('option_a'),
            option_b=request.form.get('option_b'),
            option_c=request.form.get('option_c'),
            option_d=request.form.get('option_d'),
            correct_answer=request.form.get('correct_answer'),
            points=int(request.form.get('points', 1))
        )
        db.session.add(question)
        db.session.commit()
        flash('Question added successfully!', 'success')
        return redirect(url_for('employer.manage_exam_questions', exam_id=exam_id))
    
    exam = MCQExam.query.get_or_404(exam_id)
    return render_template('exam/add_exam_question.html', exam=exam)


@bp.route('/applications')
def employer_applications():
    if 'user_id' not in session or session['user_type'] != 'employer':
        return redirect(url_for('auth.login'))
    
    user = User.query.get(session['user_id'])
    company = user.company
    
    # Check if company exists
    if not company:
        flash('Company profile not found. Please complete your company profile first.', 'error')
        return redirect(url_for('employer.employer_dashboard'))
    
    # Get applications with filters
    status_filter = request.args.get('status', '')
    job_filter = request.args.get('job_id', '')
    
    query = db.session.query(JobApplication, JobPosting, CandidateProfile, User).join(
        JobPosting, JobApplication.job_id == JobPosting.id
    ).join(
        CandidateProfile, JobApplication.candidate_id == CandidateProfile.id
    ).join(
        User, CandidateProfile.user_id == User.id
    ).filter(
        JobPosting.company_id == company.id
    )

    if status_filter:
        query = query.filter(JobApplication.application_status == status_filter)
    
    if job_filter:
        query = query.filter(JobPosting.id == int(job_filter))
    
    applications_raw = query.order_by(JobApplication.applied_at.desc()).all()
    
    # Calculate match scores for each application
    applications = []
    for app, job, candidate, candidate_user in applications_raw:
        match_score = calculate_job_match_score(candidate.id, job.id)
        applications.append((app, job, candidate, candidate_user, match_score))
    
    # Get company jobs for filter
    company_jobs = JobPosting.query.filter_by(company_id=company.id).all()
    
    return render_template('employer/employer_applications.html',
        applications=applications,
        company_jobs=company_jobs,
        company=company,
        user=user,
        status_filter=status_filter,
        job_filter=job_filter)


@bp.route('/application/<int:application_id>')
def employer_view_application(application_id):
    if 'user_id' not in session or session['user_type'] != 'employer':
        return redirect(url_for('auth.login'))
    
    application_data = db.session.query(
        JobApplication, JobPosting, CandidateProfile, User
    ).join(
        JobPosting, JobApplication.job_id == JobPosting.id
    ).join(
        CandidateProfile, JobApplication.candidate_id == CandidateProfile.id
    ).join(
        User, CandidateProfile.user_id == User.id
    ).filter(
        JobApplication.id == application_id
    ).first()
    
    if not application_data:
        flash('Application not found', 'error')
        return redirect(url_for('employer.employer_applications'))
    
    application, job, candidate, user = application_data
    
    # Verify this application belongs to employer's company
    employer = User.query.get(session['user_id'])
    if job.company_id != employer.company.id:
        flash('Unauthorized access', 'error')
        return redirect(url_for('employer.employer_applications'))
    
    # Get candidate skills
    candidate_skills = db.session.query(CandidateSkill, Skill).join(Skill).filter(
        CandidateSkill.candidate_id == candidate.id
    ).all()
    
    # Get job required skills
    required_skills = db.session.query(JobRequiredSkill, Skill).join(Skill).filter(
        JobRequiredSkill.job_id == job.id
    ).all()
    
    # Get application status history
    status_history = ApplicationStatusHistory.query.filter_by(
        application_id=application_id
    ).order_by(ApplicationStatusHistory.changed_at.desc()).all()
    
    # Calculate match score
    match_score = calculate_job_match_score(candidate.id, job.id)
    
    # Get available interviewers for recommendation
    available_interviewers = User.query.filter_by(
        user_type='interviewer', is_active=True
    ).all()
    
    # Get existing interviewer recommendations
    interviewer_recommendations = InterviewerRecommendation.query.filter_by(
        application_id=application_id
    ).all()
    
    return render_template('employer/employer_view_application.html',
                         application=application,
                         job=job,
                         candidate=candidate,
                         user=user,
                         candidate_skills=candidate_skills,
                         required_skills=required_skills,
                         status_history=status_history,
                         match_score=match_score,
                         available_interviewers=available_interviewers,
                         interviewer_recommendations=interviewer_recommendations)


@bp.route('/application/<int:application_id>/update_status', methods=['POST'])
def update_application_status(application_id):
    if 'user_id' not in session or session['user_type'] != 'employer':
        return redirect(url_for('auth.login'))
    
    application = JobApplication.query.get_or_404(application_id)
    
    # Verify ownership
    employer = User.query.get(session['user_id'])
    if application.job.company_id != employer.company.id:
        flash('Unauthorized access', 'error')
        return redirect(url_for('employer.employer_applications'))
    
    old_status = application.application_status
    new_status = request.form['status']
    notes = request.form.get('notes', '')
    
    try:
        # Update application status
        application.application_status = new_status
        
        # Create status history
        status_history = ApplicationStatusHistory(
            application_id=application_id,
            old_status=old_status,
            new_status=new_status,
            changed_by=session['user_id'],
            notes=notes
        )
        db.session.add(status_history)
        
        # Log activity
        log_activity('job_applications', 'UPDATE', application_id,
                    old_values={'application_status': old_status},
                    new_values={'application_status': new_status},
                    user_id=session['user_id'])
        
        # Notify candidate
        candidate_user = application.candidate.user
        create_notification(
            candidate_user.id,
            'Application Status Updated',
            f'Your application for {application.job.title} has been updated to: {new_status}',
            'application',
            url_for('candidate.candidate_applications')
        )
        
        db.session.commit()
        
        flash('Application status updated successfully', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating status: {str(e)}', 'error')
    
    return redirect(url_for('employer.employer_view_application', application_id=application_id))


@bp.route('/download_cv/<int:candidate_id>')
def download_cv(candidate_id):
    if 'user_id' not in session or session['user_type'] != 'employer':
        return redirect(url_for('auth.login'))
    
    # Get candidate profile
    candidate = CandidateProfile.query.get_or_404(candidate_id)
    
    # Verify employer has access to this candidate's CV (through applications)
    employer = User.query.get(session['user_id'])
    company = employer.company
    
    # Check if there's an application from this candidate to any of the employer's jobs
    application_exists = db.session.query(JobApplication).join(
        JobPosting, JobApplication.job_id == JobPosting.id
    ).filter(
        JobApplication.candidate_id == candidate_id,
        JobPosting.company_id == company.id
    ).first()
    
    if not application_exists:
        flash('You do not have permission to download this CV', 'error')
        return redirect(url_for('employer.employer_applications'))
    
    # Check if CV exists
    if not candidate.cv_content or not candidate.cv_filename:
        flash('CV not found for this candidate', 'error')
        return redirect(url_for('employer.employer_applications'))
    
    try:
        # Log the download activity
        log_activity('candidate_profiles', 'DOWNLOAD_CV', candidate_id,
                    new_values={'downloaded_by': session['user_id']},
                    user_id=session['user_id'])
        
        # Return the file with proper headers to force download
        response = Response(
            candidate.cv_content,
            mimetype=candidate.cv_mimetype or 'application/octet-stream'
        )
        response.headers['Content-Disposition'] = f'attachment; filename="{candidate.cv_filename}"'
        response.headers['Content-Length'] = len(candidate.cv_content)
        return response
    except Exception as e:
        flash(f'Error downloading CV: {str(e)}', 'error')
        return redirect(url_for('employer.employer_applications'))


@bp.route('/recommend_interviewer/<int:application_id>', methods=['POST'])
def recommend_interviewer(application_id):
    if 'user_id' not in session or session['user_type'] != 'employer':
        return redirect(url_for('auth.login'))
    
    # Verify application belongs to employer
    application = db.session.query(JobApplication).join(
        JobPosting, JobApplication.job_id == JobPosting.id
    ).filter(
        JobApplication.id == application_id,
        JobPosting.company_id == User.query.get(session['user_id']).company.id
    ).first()
    
    if not application:
        flash('Application not found or unauthorized access', 'error')
        return redirect(url_for('employer.employer_applications'))
    
    interviewer_id = request.form.get('interviewer_id')
    recommendation_notes = request.form.get('recommendation_notes', '')
    
    if not interviewer_id:
        flash('Please select an interviewer', 'error')
        return redirect(url_for('employer.employer_view_application', application_id=application_id))
    
    # Check if recommendation already exists
    existing_recommendation = InterviewerRecommendation.query.filter_by(
        application_id=application_id,
        interviewer_id=interviewer_id,
        status='pending'
    ).first()
    
    if existing_recommendation:
        flash('Recommendation already sent to this interviewer', 'warning')
        return redirect(url_for('employer.employer_view_application', application_id=application_id))
    
    try:
        # Create recommendation (pending)
        recommendation = InterviewerRecommendation(
            application_id=application_id,
            recommended_by=session['user_id'],
            interviewer_id=int(interviewer_id),
            recommendation_notes=recommendation_notes,
            status='pending'
        )
        
        db.session.add(recommendation)
        db.session.flush()
        
        # Log activity
        log_activity('interviewer_recommendations', 'INSERT', recommendation.id,
            new_values={
                'application_id': application_id,
                'interviewer_id': interviewer_id,
                'recommended_by': session['user_id']
            },
            user_id=session['user_id'])

        # Notify ADMIN/MANAGER (not interviewer)
        interviewer = User.query.get(interviewer_id)
        employer = User.query.get(session['user_id'])
        admins = User.query.filter(User.user_type.in_(['admin', 'manager'])).all()
        for admin in admins:
            create_notification(
                admin.id,
                'New Interviewer Recommendation',
                f'Employer {employer.first_name} {employer.last_name} has recommended {interviewer.first_name} {interviewer.last_name} for interviewing candidate {application.candidate.user.first_name} {application.candidate.user.last_name} (Job: {application.job.title}).',
                'system',
                url_for('admin.schedule_interview', application_id=application_id)
            )
        db.session.commit()
        flash('Interviewer recommendation submitted to manager for approval and scheduling.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error sending recommendation: {str(e)}', 'error')
    return redirect(url_for('employer.employer_view_application', application_id=application_id))
