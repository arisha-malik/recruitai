import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User, UserRole
from app.models.job import Job, JobStatus, MatchingStatus
from app.schemas.job import JobCreate, JobUpdate, JobOut
from app.dependencies import get_current_user, RoleChecker
from app.services.domain_service import normalize_job_domain

router = APIRouter(prefix="/jobs", tags=["Jobs"])

@router.get(
    "/", 
    response_model=List[JobOut],
    dependencies=[Depends(RoleChecker([UserRole.ADMIN, UserRole.RECRUITER, UserRole.HIRING_MANAGER, UserRole.INTERVIEWER]))]
)
def list_jobs(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[JobStatus] = Query(None, alias="status"),
    department: Optional[str] = Query(None),
    experience_level: Optional[str] = Query(None),
    search: Optional[str] = Query(None, description="Search by job title"),
    db: Session = Depends(get_db)
):
    query = db.query(Job)
    if status_filter:
        query = query.filter(Job.status == status_filter)
    if department:
        query = query.filter(Job.department.ilike(f"%{department}%"))
    if experience_level:
        query = query.filter(Job.experience_level.ilike(f"%{experience_level}%"))
    if search:
        query = query.filter(Job.title.ilike(f"%{search}%"))
        
    jobs = query.offset(skip).limit(limit).all()
    return jobs

@router.get(
    "/{job_id}", 
    response_model=JobOut,
    dependencies=[Depends(RoleChecker([UserRole.ADMIN, UserRole.RECRUITER, UserRole.HIRING_MANAGER, UserRole.INTERVIEWER]))]
)
def get_job(job_id: str, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    return job

@router.post(
    "/", 
    response_model=JobOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RoleChecker([UserRole.ADMIN, UserRole.RECRUITER, UserRole.HIRING_MANAGER]))]
)
def create_job(
    job_in: JobCreate, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    db_job = Job(
        id=str(uuid.uuid4()),
        title=job_in.title,
        department=job_in.department,
        location=job_in.location,
        employment_type=job_in.employment_type,
        experience_level=job_in.experience_level,
        description=job_in.description,
        required_skills=job_in.required_skills or [],
        domain=job_in.domain if job_in.domain else normalize_job_domain(
            title=job_in.title,
            department=job_in.department,
            description=job_in.description,
            skills=job_in.required_skills
        ),
        status=job_in.status or JobStatus.DRAFT,
        created_by_id=current_user.id
    )
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job

@router.patch(
    "/{job_id}", 
    response_model=JobOut,
    dependencies=[Depends(RoleChecker([UserRole.ADMIN, UserRole.RECRUITER, UserRole.HIRING_MANAGER]))]
)
def update_job(
    job_id: str, 
    job_in: JobUpdate, 
    db: Session = Depends(get_db)
):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
        
    update_data = job_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(job, field, value)
        
    db.commit()
    db.refresh(job)
    return job

@router.delete(
    "/{job_id}", 
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(RoleChecker([UserRole.ADMIN, UserRole.RECRUITER]))]
)
def delete_job(job_id: str, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    if job.matching_status == MatchingStatus.MATCHING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete job while candidate matching is in progress."
        )
    db.delete(job)
    db.commit()
    return None
