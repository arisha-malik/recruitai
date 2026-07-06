import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import cast, String
from app.database import get_db
from app.models.user import User, UserRole
from app.models.candidate import Candidate
from app.schemas.candidate import CandidateCreate, CandidateUpdate, CandidateOut
from app.dependencies import get_current_user, RoleChecker
from app.services.domain_service import normalize_candidate_domain
from app.models.domain import DomainCategory

router = APIRouter(prefix="/candidates", tags=["Candidates"])

@router.get(
    "/", 
    response_model=List[CandidateOut],
    dependencies=[Depends(RoleChecker([UserRole.ADMIN, UserRole.RECRUITER, UserRole.HIRING_MANAGER]))]
)
def list_candidates(
    skip: int = 0,
    limit: int = 100,
    skill: Optional[str] = Query(None, description="Filter candidates by skill"),
    location: Optional[str] = Query(None, description="Filter candidates by location"),
    min_experience: Optional[float] = Query(None, description="Minimum experience in years"),
    max_experience: Optional[float] = Query(None, description="Maximum experience in years"),
    domain: Optional[str] = Query(None, description="Filter candidates by domain or field"),
    education_level: Optional[str] = Query(None, description="Filter candidates by education level"),
    notice_period: Optional[str] = Query(None, description="Filter candidates by notice period"),
    db: Session = Depends(get_db)
):
    query = db.query(Candidate)
    
    if skill:
        # PostgreSQL JSON array contains check, or simple string query for fallback
        # To make it database agnostic (working on SQLite and Postgres), we use a LIKE filter on serialized representation
        # or list parsing
        query = query.filter(cast(Candidate.skills, String).ilike(f"%{skill}%"))
    if location:
        query = query.filter(Candidate.current_location.ilike(f"%{location}%"))
    if min_experience is not None:
        query = query.filter(Candidate.total_experience_years >= min_experience)
    if max_experience is not None:
        query = query.filter(Candidate.total_experience_years <= max_experience)
    if domain:
        query = query.filter(Candidate.domain == domain)
    if education_level:
        query = query.filter(Candidate.education_level.ilike(f"%{education_level}%"))
    if notice_period:
        query = query.filter(Candidate.notice_period.ilike(f"%{notice_period}%"))
        
    candidates = query.offset(skip).limit(limit).all()
    return candidates

@router.get(
    "/{candidate_id}", 
    response_model=CandidateOut,
    dependencies=[Depends(RoleChecker([UserRole.ADMIN, UserRole.RECRUITER, UserRole.HIRING_MANAGER]))]
)
def get_candidate(candidate_id: str, db: Session = Depends(get_db)):
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found"
        )
    return candidate

@router.post(
    "/", 
    response_model=CandidateOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RoleChecker([UserRole.ADMIN, UserRole.RECRUITER]))]
)
def create_candidate(candidate_in: CandidateCreate, db: Session = Depends(get_db)):
    # Check if candidate email exists
    existing = db.query(Candidate).filter(Candidate.email == candidate_in.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Candidate with this email already exists"
        )
        
    db_candidate = Candidate(
        id=str(uuid.uuid4()),
        first_name=candidate_in.first_name,
        last_name=candidate_in.last_name,
        email=candidate_in.email,
        phone=candidate_in.phone,
        current_company=candidate_in.current_company,
        current_location=candidate_in.current_location,
        total_experience_years=candidate_in.total_experience_years,
        domain=candidate_in.domain if candidate_in.domain else normalize_candidate_domain(
            title=candidate_in.current_company,
            skills=candidate_in.skills
        ),
        education_level=candidate_in.education_level,
        notice_period=candidate_in.notice_period,
        skills=candidate_in.skills or [],
        source=candidate_in.source
    )
    db.add(db_candidate)
    db.commit()
    db.refresh(db_candidate)
    return db_candidate

@router.patch(
    "/{candidate_id}", 
    response_model=CandidateOut,
    dependencies=[Depends(RoleChecker([UserRole.ADMIN, UserRole.RECRUITER]))]
)
def update_candidate(
    candidate_id: str, 
    candidate_in: CandidateUpdate, 
    db: Session = Depends(get_db)
):
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found"
        )
        
    update_data = candidate_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(candidate, field, value)
        
    db.commit()
    db.refresh(candidate)
    return candidate

@router.delete(
    "/{candidate_id}", 
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(RoleChecker([UserRole.ADMIN, UserRole.RECRUITER]))]
)
def delete_candidate(candidate_id: str, db: Session = Depends(get_db)):
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found"
        )
    db.delete(candidate)
    db.commit()
    return None
