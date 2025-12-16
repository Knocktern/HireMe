from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from sqlalchemy import and_, or_
from datetime import datetime
from werkzeug.utils import secure_filename
import os
from extensions import db
from models import (
    User, CandidateProfile, JobPosting, JobApplication, Company, 
    MCQExam, ExamAttempt, Skill, CandidateSkill, JobRequiredSkill, 
    Notification, InterviewRoom
)
from services import create_notification, log_activity, calculate_job_match_score
from utils import allowed_file

candidate_bp = Blueprint('candidate', __name__)

def get_job_recommendations(candidate_id):
    """Get personalized job recommendations for a candidate"""
    candidate = CandidateProfile.query.get(candidate_id)
    if not candidate:
        return []
    
    # Get jobs the candidate hasn't applied to
    applied_job_ids = db.session.query(JobApplication.job_id).filter_by(
        candidate_id=candidate_id
    ).subquery()
    
    available_jobs = db.session.query(JobPosting, Company).join(
        Company, JobPosting.company_id == Company.id
    ).filter(
        JobPosting.is_active == True,
        ~JobPosting.id.in_(applied_job_ids)
    ).all()
    
    # Calculate match scores and sort
    job_matches = []
    for job, company in available_jobs:
        match_score = calculate_job_match_score(candidate_id, job.id)
        if match_score > 30:  # Only show jobs with decent match
            job_matches.append({
                'job': job,
                'company': company,
                'match_score': match_score
            })
    
    # Sort by match score
    job_matches.sort(key=lambda x: x['match_score'], reverse=True)
    
    return job_matches[:10]  # Return top 10 matches
