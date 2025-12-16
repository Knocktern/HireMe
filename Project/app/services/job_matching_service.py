from decimal import Decimal
from extensions import db
from models import CandidateProfile, JobPosting, JobRequiredSkill, CandidateSkill

def calculate_job_match_score(candidate_id, job_id):
    """Calculate match score between candidate and job"""
    candidate = CandidateProfile.query.get(candidate_id)
    job = JobPosting.query.get(job_id)
    
    if not candidate or not job:
        return 0

    score = 0
    max_score = 100

    # Experience match (30 points)
    if candidate.experience_years >= job.experience_required:
        score += 30
    elif candidate.experience_years >= job.experience_required * 0.7:
        score += 20
    elif candidate.experience_years >= job.experience_required * 0.5:
        score += 10

    # Skills match (50 points)
    required_skills = JobRequiredSkill.query.filter_by(job_id=job_id).all()
    candidate_skills = CandidateSkill.query.filter_by(candidate_id=candidate_id).all()
    candidate_skill_ids = [cs.skill_id for cs in candidate_skills]

    if required_skills:
        matched_skills = 0
        total_weight = 0
        for req_skill in required_skills:
            weight = 3 if req_skill.importance == 'Required' else 2 if req_skill.importance == 'Preferred' else 1
            total_weight += weight
            if req_skill.skill_id in candidate_skill_ids:
                matched_skills += weight

        if total_weight > 0:
            score += int((matched_skills / total_weight) * 50)
    else:
        score += 25  # No specific skills required

    # Location match (10 points)
    if candidate.location and job.location:
        if candidate.location.lower() in job.location.lower() or job.location.lower() in candidate.location.lower():
            score += 10
        else:
            score += 5  # Partial match

    # Salary expectation match (10 points)
    if candidate.salary_expectation and job.salary_min and job.salary_max:
        multiplier = Decimal('1.2')
        if job.salary_min <= candidate.salary_expectation <= job.salary_max:
            score += 10
        elif candidate.salary_expectation <= job.salary_max * multiplier:
            score += 5

    return min(score, max_score)
