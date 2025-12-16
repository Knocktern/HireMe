from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from extensions import db
from models import (
    User, ActivityLog, Notification, InterviewRoom, InterviewParticipant, 
    InterviewFeedback, CodeSession, InterviewerRecommendation,
    JobApplication, JobPosting, Company, CandidateProfile
)
from datetime import datetime
import json
import time

bp = Blueprint('interview', __name__)

# --- INTERVIEW ROOM ROUTES ---

@bp.route('/interview/<room_code>')
def join_interview(room_code):
    """Join interview room - simplified approach"""
    try:
        # Get interview room from database using existing models
        room = InterviewRoom.query.filter_by(room_code=room_code).first_or_404()
        
        # Check if user is authorized to join
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        
        participant = InterviewParticipant.query.filter_by(
            room_id=room.id,
            user_id=session['user_id']
        ).first()
        
        if not participant:
            flash('You are not authorized to join this interview', 'error')
            return redirect(url_for('main.index'))
        
        # Get all participants
        participants = db.session.query(InterviewParticipant, User).join(User).filter(
            InterviewParticipant.room_id == room.id
        ).all()
        
        return render_template('interviewer/interview_room.html', 
                             room=room, 
                             participants=participants,
                             current_user_role=participant.role)
        
    except Exception as e:
        flash(f'Error loading interview room: {e}', 'error')
        return redirect(url_for('main.index'))

@bp.route('/interview/<room_code>/feedback', methods=['GET', 'POST'])
def interview_feedback(room_code):
    if 'user_id' not in session or session['user_type'] != 'interviewer':
        return redirect(url_for('auth.login'))
        
    room = InterviewRoom.query.filter_by(room_code=room_code).first_or_404()
    
    if request.method == 'POST':
        feedback = InterviewFeedback(
            room_id=room.id,
            interviewer_id=session['user_id'],
            candidate_id=room.application.candidate.user_id,
            technical_score=int(request.form.get('technical_score', 0)),
            communication_score=int(request.form.get('communication_score', 0)),
            problem_solving_score=int(request.form.get('problem_solving_score', 0)),
            overall_rating=request.form.get('overall_rating'),
            feedback_text=request.form.get('feedback_text'),
            recommendation=request.form.get('recommendation')
        )
        db.session.add(feedback)
        db.session.commit()
        
        flash('Feedback submitted successfully', 'success')
        return redirect(url_for('interviewer.interviewer_dashboard'))
        
    return render_template('interviewer/interview_feedback.html', room=room)
