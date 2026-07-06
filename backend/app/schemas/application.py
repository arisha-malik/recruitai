from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
from app.models.application import ApplicationStatus

class ApplicationCreate(BaseModel):
    candidate_id: str
    job_id: str

class ApplicationUpdateStatus(BaseModel):
    status: ApplicationStatus

class ApplicationDecisionRequest(BaseModel):
    decision: str  # SHORTLIST | REJECT | MAYBE

class MatchResultOut(BaseModel):
    id: str
    candidate_id: str
    job_id: str
    application_id: Optional[str] = None
    match_percentage: float
    skill_match_analysis: str
    missing_skills: Optional[List[str]] = None
    experience_delta: str
    location_fit: str
    notice_period_fit: str
    final_recommendation: str
    created_at: datetime

    class Config:
        from_attributes = True

# Simple representations to avoid circular imports
class CandidateMini(BaseModel):
    id: str
    first_name: str
    last_name: str
    email: str

    class Config:
        from_attributes = True

class JobMini(BaseModel):
    id: str
    title: str
    department: str
    location: str

    class Config:
        from_attributes = True

class ApplicationOut(BaseModel):
    id: str
    candidate_id: str
    job_id: str
    status: ApplicationStatus
    applied_at: datetime
    updated_at: datetime
    candidate: Optional[CandidateMini] = None
    job: Optional[JobMini] = None
    match_results: List[MatchResultOut] = []

    class Config:
        from_attributes = True
