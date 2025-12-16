from extensions import db
from datetime import datetime

class MCQExam(db.Model):
    __tablename__ = 'mcq_exams'
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('job_postings.id'), nullable=False)
    exam_title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    duration_minutes = db.Column(db.Integer, default=60)
    total_questions = db.Column(db.Integer, default=0)
    passing_score = db.Column(db.Numeric(5, 2), default=60.00)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    questions = db.relationship('MCQQuestion', backref='exam', lazy=True)

class MCQQuestion(db.Model):
    __tablename__ = 'mcq_questions'
    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey('mcq_exams.id'), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.String(500), nullable=False)
    option_b = db.Column(db.String(500), nullable=False)
    option_c = db.Column(db.String(500), nullable=False)
    option_d = db.Column(db.String(500), nullable=False)
    correct_answer = db.Column(db.Enum('A', 'B', 'C', 'D'), nullable=False)
    points = db.Column(db.Integer, default=1)
    difficulty_level = db.Column(db.Enum('Easy', 'Medium', 'Hard'), default='Medium')
    category = db.Column(db.String(100))

class ExamAttempt(db.Model):
    __tablename__ = 'exam_attempts'
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidate_profiles.id'), nullable=False)
    exam_id = db.Column(db.Integer, db.ForeignKey('mcq_exams.id'), nullable=False)
    score = db.Column(db.Numeric(5, 2))
    total_questions = db.Column(db.Integer)
    correct_answers = db.Column(db.Integer)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    status = db.Column(db.Enum('in_progress', 'completed', 'abandoned'), default='in_progress')
    time_spent = db.Column(db.Integer)  # in seconds

class CandidateAnswer(db.Model):
    __tablename__ = 'candidate_answers'
    id = db.Column(db.Integer, primary_key=True)
    attempt_id = db.Column(db.Integer, db.ForeignKey('exam_attempts.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('mcq_questions.id'), nullable=False)
    selected_answer = db.Column(db.Enum('A', 'B', 'C', 'D'))
    is_correct = db.Column(db.Boolean)
    time_spent = db.Column(db.Integer)  # time spent on this question in seconds
