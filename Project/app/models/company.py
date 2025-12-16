from extensions import db
from datetime import datetime

class Company(db.Model):
    __tablename__ = 'companies'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    company_name = db.Column(db.String(255), nullable=False)
    industry = db.Column(db.String(100))
    company_size = db.Column(db.Enum('1-10', '11-50', '51-200', '201-500', '500+'))
    location = db.Column(db.String(255))
    description = db.Column(db.Text)
    website = db.Column(db.String(255))
    logo = db.Column(db.LargeBinary)
    logo_filename = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    job_postings = db.relationship('JobPosting', backref='company', lazy=True)

