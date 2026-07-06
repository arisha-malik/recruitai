import os
import sys

# Add backend directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models.job import Job
from app.models.candidate import Candidate, ParsedResumeData
from app.models.domain import DomainCategory
from app.services.domain_service import normalize_job_domain, normalize_candidate_domain

def backfill_domains():
    db = SessionLocal()
    try:
        # Backfill Jobs
        print("Backfilling Jobs...")
        jobs = db.query(Job).all()
        jobs_updated = 0
        for job in jobs:
            if not job.domain or job.domain == DomainCategory.OTHER:
                new_domain = normalize_job_domain(
                    title=job.title,
                    department=job.department,
                    description=job.description,
                    skills=job.required_skills
                )
                if new_domain != job.domain:
                    job.domain = new_domain
                    jobs_updated += 1
        
        # Backfill Candidates
        print("Backfilling Candidates...")
        candidates = db.query(Candidate).all()
        candidates_updated = 0
        for candidate in candidates:
            if not candidate.domain or candidate.domain == DomainCategory.OTHER:
                # Get raw text from parsed resume if available
                # Assuming one resume for simplicity in backfill
                parsed = db.query(ParsedResumeData).join(ParsedResumeData.resume).filter(
                    ParsedResumeData.resume.has(candidate_id=candidate.id)
                ).first()
                text = ""
                if parsed and parsed.raw_json:
                    text = str(parsed.raw_json)

                new_domain = normalize_candidate_domain(
                    title=candidate.current_company,
                    skills=candidate.skills,
                    education=candidate.education_level,
                    text=text
                )
                if new_domain != candidate.domain:
                    candidate.domain = new_domain
                    candidates_updated += 1

        db.commit()
        print(f"Backfill complete! Updated {jobs_updated} jobs and {candidates_updated} candidates.")
        
    except Exception as e:
        db.rollback()
        print(f"Error during backfill: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    backfill_domains()
