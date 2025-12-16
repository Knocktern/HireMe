from extensions import db
from datetime import datetime


class InterviewerProfile(db.Model):
    """Main profile for interviewers (both independent experts and in-house)"""
    __tablename__ = 'interviewer_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    
    # Profile Information
    headline = db.Column(db.String(255))  # e.g., "Senior React Developer | 10+ Years Experience"
    bio = db.Column(db.Text)
    experience_years = db.Column(db.Integer, default=0)
    linkedin_url = db.Column(db.String(500))
    
    # CV/Resume
    cv_file_path = db.Column(db.String(500))
    cv_content = db.Column(db.LargeBinary)
    cv_filename = db.Column(db.String(255))
    cv_mimetype = db.Column(db.String(100))
    
    # Experience Proof Document
    experience_proof_path = db.Column(db.String(500))
    experience_proof_content = db.Column(db.LargeBinary)
    experience_proof_filename = db.Column(db.String(255))
    experience_proof_mimetype = db.Column(db.String(100))
    
    # Interviewer Type
    interviewer_type = db.Column(db.Enum('independent', 'in_house'), default='independent')
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=True)  # For in-house interviewers
    
    # Payment
    hourly_rate = db.Column(db.Numeric(10, 2), default=0)  # Rate per hour
    currency = db.Column(db.String(10), default='USD')
    
    # Status & Verification
    approval_status = db.Column(db.Enum('pending', 'approved', 'rejected'), default='pending')
    rejection_reason = db.Column(db.Text)
    is_verified = db.Column(db.Boolean, default=False)  # Verification badge
    is_active = db.Column(db.Boolean, default=True)
    is_available = db.Column(db.Boolean, default=True)  # Currently accepting interviews
    
    # Stats
    total_interviews = db.Column(db.Integer, default=0)
    total_earnings = db.Column(db.Numeric(12, 2), default=0)
    average_rating = db.Column(db.Numeric(3, 2), default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    approved_at = db.Column(db.DateTime)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('interviewer_profile', uselist=False))
    company = db.relationship('Company', backref='in_house_interviewers')
    skills = db.relationship('InterviewerSkill', backref='interviewer', lazy=True, cascade='all, delete-orphan')
    industries = db.relationship('InterviewerIndustry', backref='interviewer', lazy=True, cascade='all, delete-orphan')
    certifications = db.relationship('InterviewerCertification', backref='interviewer', lazy=True, cascade='all, delete-orphan')
    availabilities = db.relationship('InterviewerAvailability', backref='interviewer', lazy=True, cascade='all, delete-orphan')
    earnings = db.relationship('InterviewerEarning', backref='interviewer', lazy=True)
    reviews = db.relationship('InterviewerReview', backref='interviewer', lazy=True)
    
    def __repr__(self):
        return f'<InterviewerProfile {self.id} - User {self.user_id}>'
    
    @property
    def full_name(self):
        return f"{self.user.first_name} {self.user.last_name}" if self.user else "Unknown"
    
    @property
    def skill_names(self):
        return [s.skill.skill_name for s in self.skills if s.skill]
    
    @property
    def industry_names(self):
        return [i.industry_name for i in self.industries]


class InterviewerSkill(db.Model):
    """Skills that interviewer can conduct interviews for"""
    __tablename__ = 'interviewer_skills'
    
    id = db.Column(db.Integer, primary_key=True)
    interviewer_id = db.Column(db.Integer, db.ForeignKey('interviewer_profiles.id'), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey('skills.id'), nullable=False)
    proficiency_level = db.Column(db.Enum('Intermediate', 'Advanced', 'Expert'), default='Advanced')
    years_experience = db.Column(db.Integer, default=0)
    can_interview = db.Column(db.Boolean, default=True)  # Can interview for this skill
    
    # Relationship
    skill = db.relationship('Skill', backref='interviewer_skills')
    
    __table_args__ = (
        db.UniqueConstraint('interviewer_id', 'skill_id', name='unique_interviewer_skill'),
    )


class InterviewerIndustry(db.Model):
    """Industries the interviewer has experience in"""
    __tablename__ = 'interviewer_industries'
    
    id = db.Column(db.Integer, primary_key=True)
    interviewer_id = db.Column(db.Integer, db.ForeignKey('interviewer_profiles.id'), nullable=False)
    industry_name = db.Column(db.String(100), nullable=False)
    years_experience = db.Column(db.Integer, default=0)
    
    __table_args__ = (
        db.UniqueConstraint('interviewer_id', 'industry_name', name='unique_interviewer_industry'),
    )


class InterviewerCertification(db.Model):
    """Certifications and credentials of interviewer"""
    __tablename__ = 'interviewer_certifications'
    
    id = db.Column(db.Integer, primary_key=True)
    interviewer_id = db.Column(db.Integer, db.ForeignKey('interviewer_profiles.id'), nullable=False)
    
    certification_name = db.Column(db.String(255), nullable=False)
    issuing_organization = db.Column(db.String(255))
    issue_date = db.Column(db.Date)
    expiry_date = db.Column(db.Date)
    credential_id = db.Column(db.String(255))
    credential_url = db.Column(db.String(500))
    
    # Certificate file
    certificate_file_path = db.Column(db.String(500))
    certificate_content = db.Column(db.LargeBinary)
    certificate_filename = db.Column(db.String(255))
    certificate_mimetype = db.Column(db.String(100))
    
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class InterviewerAvailability(db.Model):
    """Weekly availability slots for interviewers"""
    __tablename__ = 'interviewer_availabilities'
    
    id = db.Column(db.Integer, primary_key=True)
    interviewer_id = db.Column(db.Integer, db.ForeignKey('interviewer_profiles.id'), nullable=False)
    
    day_of_week = db.Column(db.Integer, nullable=False)  # 0=Monday, 6=Sunday
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    timezone = db.Column(db.String(50), default='UTC')
    is_active = db.Column(db.Boolean, default=True)
    
    __table_args__ = (
        db.CheckConstraint('day_of_week >= 0 AND day_of_week <= 6', name='valid_day_of_week'),
    )


class InterviewerEarning(db.Model):
    """Track earnings for each completed interview"""
    __tablename__ = 'interviewer_earnings'
    
    id = db.Column(db.Integer, primary_key=True)
    interviewer_id = db.Column(db.Integer, db.ForeignKey('interviewer_profiles.id'), nullable=False)
    interview_room_id = db.Column(db.Integer, db.ForeignKey('interview_rooms.id'), nullable=False)
    
    duration_minutes = db.Column(db.Integer, default=0)
    hourly_rate = db.Column(db.Numeric(10, 2), nullable=False)
    amount_earned = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(10), default='USD')
    
    status = db.Column(db.Enum('pending', 'confirmed', 'paid'), default='pending')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    confirmed_at = db.Column(db.DateTime)
    paid_at = db.Column(db.DateTime)
    
    # Relationships
    interview_room = db.relationship('InterviewRoom', backref='interviewer_earnings')


class InterviewerReview(db.Model):
    """Reviews/ratings from employers after interviews"""
    __tablename__ = 'interviewer_reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    interviewer_id = db.Column(db.Integer, db.ForeignKey('interviewer_profiles.id'), nullable=False)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # Employer/HR who reviews
    interview_room_id = db.Column(db.Integer, db.ForeignKey('interview_rooms.id'), nullable=True)
    
    # Ratings (1-5)
    professionalism_rating = db.Column(db.Integer)
    technical_accuracy_rating = db.Column(db.Integer)
    communication_rating = db.Column(db.Integer)
    punctuality_rating = db.Column(db.Integer)
    overall_rating = db.Column(db.Integer)
    
    review_text = db.Column(db.Text)
    would_hire_again = db.Column(db.Boolean, default=True)
    
    is_public = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    reviewer = db.relationship('User', backref='interviewer_reviews_given')
    interview_room = db.relationship('InterviewRoom', backref='interviewer_reviews')
    
    __table_args__ = (
        db.CheckConstraint('overall_rating >= 1 AND overall_rating <= 5', name='valid_overall_rating'),
    )


class InterviewerApplication(db.Model):
    """Application to become an expert interviewer (for admin review)"""
    __tablename__ = 'interviewer_applications'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Applicant info (before user creation)
    email = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    
    # Professional info
    headline = db.Column(db.String(255))
    bio = db.Column(db.Text)
    experience_years = db.Column(db.Integer, default=0)
    linkedin_url = db.Column(db.String(500))
    hourly_rate = db.Column(db.Numeric(10, 2))
    currency = db.Column(db.String(10), default='USD')
    
    # Skills (comma-separated skill IDs or names)
    skills_json = db.Column(db.Text)  # JSON array of skill info
    industries_json = db.Column(db.Text)  # JSON array of industries
    
    # Documents
    cv_content = db.Column(db.LargeBinary)
    cv_filename = db.Column(db.String(255))
    cv_mimetype = db.Column(db.String(100))
    
    experience_proof_content = db.Column(db.LargeBinary)
    experience_proof_filename = db.Column(db.String(255))
    experience_proof_mimetype = db.Column(db.String(100))
    
    certifications_json = db.Column(db.Text)  # JSON array of certification info
    
    # Application status
    status = db.Column(db.Enum('pending', 'under_review', 'approved', 'rejected'), default='pending')
    rejection_reason = db.Column(db.Text)
    reviewed_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # After approval, link to created user
    created_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime)
    
    # Relationships
    reviewer = db.relationship('User', foreign_keys=[reviewed_by], backref='reviewed_applications')
    created_user = db.relationship('User', foreign_keys=[created_user_id], backref='interviewer_application')


class InterviewerJobRole(db.Model):
    """Job roles/positions the interviewer can conduct interviews for"""
    __tablename__ = 'interviewer_job_roles'
    
    id = db.Column(db.Integer, primary_key=True)
    interviewer_id = db.Column(db.Integer, db.ForeignKey('interviewer_profiles.id'), nullable=False)
    
    role_name = db.Column(db.String(255), nullable=False)  # e.g., "React Developer", "Backend Engineer"
    experience_level = db.Column(db.Enum('Junior', 'Mid', 'Senior', 'Lead', 'Principal', 'All Levels'), default='All Levels')
    interviews_conducted = db.Column(db.Integer, default=0)
    
    interviewer = db.relationship('InterviewerProfile', backref='job_roles')
    
    __table_args__ = (
        db.UniqueConstraint('interviewer_id', 'role_name', name='unique_interviewer_role'),
    )
