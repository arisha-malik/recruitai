import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import UserRole
from app.models.application import Application, ApplicationStatus
from app.models.candidate import Candidate
from app.models.job import Job
from app.schemas.application import ApplicationCreate, ApplicationUpdateStatus, ApplicationOut, ApplicationDecisionRequest
from app.dependencies import RoleChecker, get_current_user
from app.models.user import User
from app.services.event_service import log_recruitment_event

router = APIRouter(prefix="/applications", tags=["Applications"])

@router.get(
    "/", 
    response_model=List[ApplicationOut],
    dependencies=[Depends(RoleChecker([UserRole.ADMIN, UserRole.RECRUITER, UserRole.HIRING_MANAGER, UserRole.INTERVIEWER]))]
)
def list_applications(
    skip: int = 0,
    limit: int = 100,
    job_id: Optional[str] = Query(None),
    candidate_id: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db)
):
    query = db.query(Application)
    if job_id:
        query = query.filter(Application.job_id == job_id)
    if candidate_id:
        query = query.filter(Application.candidate_id == candidate_id)
    if status_filter:
        query = query.filter(Application.status == status_filter.upper())
        
    apps = query.offset(skip).limit(limit).all()
    return apps

@router.get(
    "/{application_id}", 
    response_model=ApplicationOut,
    dependencies=[Depends(RoleChecker([UserRole.ADMIN, UserRole.RECRUITER, UserRole.HIRING_MANAGER, UserRole.INTERVIEWER]))]
)
def get_application(application_id: str, db: Session = Depends(get_db)):
    app = db.query(Application).filter(Application.id == application_id).first()
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    return app

@router.post(
    "/", 
    response_model=ApplicationOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RoleChecker([UserRole.ADMIN, UserRole.RECRUITER]))]
)
def create_application(app_in: ApplicationCreate, db: Session = Depends(get_db)):
    # Verify candidate exists
    candidate = db.query(Candidate).filter(Candidate.id == app_in.candidate_id).first()
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found"
        )
        
    # Verify job exists
    job = db.query(Job).filter(Job.id == app_in.job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
        
    # Check if application already exists
    existing = db.query(Application).filter(
        Application.candidate_id == app_in.candidate_id,
        Application.job_id == app_in.job_id
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Candidate has already applied for this job"
        )
        
    db_app = Application(
        id=str(uuid.uuid4()),
        candidate_id=app_in.candidate_id,
        job_id=app_in.job_id,
        status=ApplicationStatus.APPLIED
    )
    db.add(db_app)
    db.commit()
    db.refresh(db_app)
    return db_app

@router.patch(
    "/{application_id}/status", 
    response_model=ApplicationOut,
    dependencies=[Depends(RoleChecker([UserRole.ADMIN, UserRole.RECRUITER, UserRole.HIRING_MANAGER]))]
)
def update_application_status(
    application_id: str, 
    status_in: ApplicationUpdateStatus, 
    db: Session = Depends(get_db)
):
    app = db.query(Application).filter(Application.id == application_id).first()
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
        
    app.status = status_in.status
    
    # Populate transition timestamps based on new status
    import datetime
    now = datetime.datetime.now(datetime.timezone.utc)
    if status_in.status == ApplicationStatus.SHORTLISTED:
        app.shortlisted_at = now
    elif status_in.status == ApplicationStatus.INTERVIEWING:
        app.interviewing_at = now
    elif status_in.status == ApplicationStatus.OFFERED:
        app.offered_at = now
    elif status_in.status == ApplicationStatus.REJECTED:
        app.rejected_at = now
        
    db.commit()
    db.refresh(app)
    return app

@router.post(
    "/{application_id}/decision", 
    response_model=ApplicationOut,
    dependencies=[Depends(RoleChecker([UserRole.ADMIN, UserRole.RECRUITER, UserRole.HIRING_MANAGER]))]
)
def save_recruiter_decision(
    application_id: str, 
    decision_in: ApplicationDecisionRequest, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    app = db.query(Application).filter(Application.id == application_id).first()
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
        
    decision = decision_in.decision.upper()
    event_type = ""
    
    import datetime
    now = datetime.datetime.now(datetime.timezone.utc)
    
    if decision == "SHORTLIST":
        app.status = ApplicationStatus.INTERVIEWING
        app.interviewing_at = now
        event_type = "CANDIDATE_SHORTLISTED"
    elif decision == "REJECT":
        app.status = ApplicationStatus.REJECTED
        app.rejected_at = now
        event_type = "CANDIDATE_REJECTED"
    elif decision == "MAYBE":
        app.status = ApplicationStatus.MAYBE
        event_type = "CANDIDATE_MARKED_MAYBE"
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid decision"
        )
        
    db.commit()
    db.refresh(app)
    
    # Log the event
    log_recruitment_event(
        db=db,
        event_type=event_type,
        candidate_id=app.candidate_id,
        job_id=app.job_id,
        application_id=app.id,
        actor_id=current_user.id,
        metadata={"decision": decision}
    )
    
    return app
