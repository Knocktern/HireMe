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
