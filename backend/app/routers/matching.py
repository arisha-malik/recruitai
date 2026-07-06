from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.config import settings
from app.database import get_db
from app.models.user import User, UserRole
from app.models.job import Job, MatchingStatus, JobStatus
from app.models.application import MatchResult, Application, ApplicationStatus
from app.models.candidate import Candidate
from app.schemas.matching import MatchRunResponse, MatchStatusResponse, MatchResultsResponse, CandidateMatchResultOut
from app.worker.tasks import run_candidate_matching_job
from app.dependencies import get_current_user, RoleChecker

router = APIRouter(prefix="/matching", tags=["Candidate Matching"])

@router.post(
    "/jobs/{job_id}/run", 
    response_model=MatchRunResponse,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(RoleChecker([UserRole.ADMIN, UserRole.RECRUITER, UserRole.HIRING_MANAGER]))]
)
def run_matching(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Trigger the candidate matching pipeline asynchronously for a job description.
    Generates Job embedding (if needed), queries Qdrant candidates vectors,
    runs LLM matching evaluation, and saves MatchResults in database.
    """
    # 1. Verify Job exists
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job record not found."
        )
        
    if not job.description or not job.required_skills:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job must have description and required skills to run matching."
        )
        
    if job.status != JobStatus.OPEN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Candidate matching can only be run for OPEN jobs."
        )
        
    if job.matching_status == MatchingStatus.MATCHING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Candidate matching is already running for this job."
        )
        
    # 2. Update job status to MATCHING
    job.matching_status = MatchingStatus.MATCHING
    job.matching_error = None
    db.commit()
    
    # 3. Trigger Celery task (synchronously if configured for local testing)
    if settings.RUN_JOBS_SYNC:
        task = run_candidate_matching_job.apply(args=(job_id, current_user.id))
    else:
        task = run_candidate_matching_job.delay(job_id, current_user.id)
    
    return {
        "matching_job_id": str(task.id),
        "job_id": job_id,
        "status": "MATCHING_STARTED"
    }

@router.get(
    "/jobs/{job_id}/status", 
    response_model=MatchStatusResponse,
    dependencies=[Depends(RoleChecker([UserRole.ADMIN, UserRole.RECRUITER, UserRole.HIRING_MANAGER, UserRole.INTERVIEWER]))]
)
def get_matching_status(
    job_id: str,
    db: Session = Depends(get_db)
):
    """
    Check status and statistics of candidate matching run for a job description.
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job record not found."
        )
        
    return {
        "job_id": job.id,
        "status": job.matching_status.value,
        "total_candidates_checked": job.total_candidates_checked,
        "total_matches_created": job.total_matches_created,
        "error_message": job.matching_error
    }

@router.get(
    "/jobs/{job_id}/results", 
    response_model=MatchResultsResponse,
    dependencies=[Depends(RoleChecker([UserRole.ADMIN, UserRole.RECRUITER, UserRole.HIRING_MANAGER, UserRole.INTERVIEWER]))]
)
def get_matching_results(
    job_id: str,
    min_score: Optional[float] = Query(None, description="Minimum match percentage"),
    recommendation: Optional[str] = Query(None, description="Final recommendation (SHORTLIST, MAYBE, REJECT)"),
    skill: Optional[str] = Query(None, description="Require a matching skill name"),
    location: Optional[str] = Query(None, description="Filter location text"),
    min_experience: Optional[float] = Query(None, description="Minimum candidate experience"),
    max_experience: Optional[float] = Query(None, description="Maximum candidate experience"),
    shortlisted: Optional[bool] = Query(None, description="Filter candidates that are currently shortlisted"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Retrieve ranked candidate matches for a job description based on LLM evaluation scoring.
    """
    # Verify Job exists
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job record not found."
        )
        
    # Build query joining MatchResult and Candidate details
    query = db.query(MatchResult).filter(MatchResult.job_id == job_id)
    query = query.join(Candidate, MatchResult.candidate_id == Candidate.id)
    
    # Apply filters
    if min_score is not None:
        query = query.filter(MatchResult.match_percentage >= min_score)
        
    if recommendation:
        query = query.filter(MatchResult.final_recommendation == recommendation.upper())
        
    if skill:
        # MatchResult matched_skills is JSON array. Filter matching substring
        query = query.filter(MatchResult.matched_skills.like(f"%{skill}%"))
        
    if location:
        query = query.filter(
            (MatchResult.location_fit.ilike(f"%{location}%")) |
            (Candidate.current_location.ilike(f"%{location}%"))
        )
        
    if min_experience is not None:
        query = query.filter(Candidate.total_experience_years >= min_experience)
        
    if max_experience is not None:
        query = query.filter(Candidate.total_experience_years <= max_experience)
        
    if shortlisted is not None:
        # Join Application and check status
        query = query.join(Application, (MatchResult.candidate_id == Application.candidate_id) & (MatchResult.job_id == Application.job_id))
        if shortlisted:
            query = query.filter(Application.status == ApplicationStatus.SHORTLISTED)
        else:
            query = query.filter(Application.status != ApplicationStatus.SHORTLISTED)
            
    # Sort: Match Percentage DESC, Vector Similarity DESC as supporting signal
    query = query.order_by(
        desc(MatchResult.match_percentage),
        desc(MatchResult.vector_similarity_score)
    )
    
    match_results = query.offset(skip).limit(limit).all()
    
    results = []
    for mr in match_results:
        cand = mr.candidate
        results.append({
            "candidate_id": mr.candidate_id,
            "application_id": mr.application_id,
            "candidate_name": f"{cand.first_name} {cand.last_name}",
            "match_percentage": mr.match_percentage,
            "skill_match_analysis": mr.skill_match_analysis,
            "matched_skills": mr.matched_skills or [],
            "missing_skills": mr.missing_skills or [],
            "experience_analysis": mr.experience_analysis,
            "experience_delta": mr.experience_delta,
            "location_fit": mr.location_fit,
            "notice_period_fit": mr.notice_period_fit,
            "strengths": mr.strengths or [],
            "concerns": mr.concerns or [],
            "final_recommendation": mr.final_recommendation,
            "summary": mr.summary
        })
        
    return {
        "job_id": job_id,
        "results": results
    }
