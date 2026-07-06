from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
from app.models.job import JobStatus, MatchingStatus
from app.models.domain import DomainCategory

class JobCreate(BaseModel):
    title: str
    department: Optional[str] = None
    location: Optional[str] = None
    employment_type: str
    experience_level: Optional[str] = None
    description: str
    required_skills: Optional[List[str]] = None
    domain: Optional[DomainCategory] = None
    status: Optional[JobStatus] = JobStatus.DRAFT

class JobUpdate(BaseModel):
    title: Optional[str] = None
    department: Optional[str] = None
    location: Optional[str] = None
    employment_type: Optional[str] = None
    experience_level: Optional[str] = None
    description: Optional[str] = None
    required_skills: Optional[List[str]] = None
    domain: Optional[DomainCategory] = None
    status: Optional[JobStatus] = None

class JobOut(BaseModel):
    id: str
    title: str
    department: Optional[str] = None
    domain: DomainCategory
    location: Optional[str] = None
    employment_type: str
    experience_level: Optional[str] = None
    description: str
    required_skills: Optional[List[str]] = None
    status: JobStatus
    matching_status: Optional[MatchingStatus] = None
    matching_error: Optional[str] = None
    created_by_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
