from extensions import db
from datetime import datetime

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
    code_sessions = db.relationship('CodeSession', backref='room', lazy=True)

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

class CodeSession(db.Model):
    __tablename__ = 'code_sessions'
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('interview_rooms.id'), nullable=False)
    session_name = db.Column(db.String(255), default='Coding Session')
    language = db.Column(db.String(50), default='javascript')
    code_content = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class InterviewerRecommendation(db.Model):
    __tablename__ = 'interviewer_recommendations'
    
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('job_applications.id'), nullable=False)
    recommended_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    interviewer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    recommendation_notes = db.Column(db.Text)
    status = db.Column(db.Enum('pending', 'accepted', 'rejected', 'not_selected'), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    application = db.relationship('JobApplication', backref='interviewer_recommendations')
    recommender = db.relationship('User', foreign_keys=[recommended_by])
    interviewer = db.relationship('User', foreign_keys=[interviewer_id])
