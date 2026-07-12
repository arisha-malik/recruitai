from datetime import datetime
from typing import List, Optional, Any
from pydantic import BaseModel, EmailStr
from app.models.domain import DomainCategory

class ParsedResumeDataOut(BaseModel):
    id: str
    resume_id: str
    full_name: Optional[str] = None
    email: Optional[str] = None
    mobile_number: Optional[str] = None
    total_experience: Optional[float] = None
    technical_skills: Optional[List[str]] = None
    education: Optional[Any] = None
    certifications: Optional[List[str]] = None
    current_company: Optional[str] = None
    current_location: Optional[str] = None
    notice_period: Optional[str] = None
    work_experience: Optional[Any] = None
    projects: Optional[Any] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ResumeOut(BaseModel):
    id: str
    file_name: str
    original_filename: Optional[str] = None
    stored_filename: Optional[str] = None
    storage_path: Optional[str] = None
    candidate_primary_designation: Optional[str] = None
    primary_skill: Optional[str] = None
    s3_key: str
    s3_bucket: str
    parsing_status: str
    created_at: datetime
    parsed_data: Optional[ParsedResumeDataOut] = None

    class Config:
        from_attributes = True

class CandidateCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: Optional[str] = None
    current_company: Optional[str] = None
    current_location: Optional[str] = None
    total_experience_years: Optional[float] = None
    domain: Optional[DomainCategory] = None
    education_level: Optional[str] = None
    notice_period: Optional[str] = None
    skills: Optional[List[str]] = None
    source: Optional[str] = None

class CandidateUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    current_company: Optional[str] = None
    current_location: Optional[str] = None
    total_experience_years: Optional[float] = None
    domain: Optional[DomainCategory] = None
    education_level: Optional[str] = None
    notice_period: Optional[str] = None
    skills: Optional[List[str]] = None
    source: Optional[str] = None

class CandidateOut(BaseModel):
    id: str
    first_name: str
    last_name: str
    email: EmailStr
    phone: Optional[str] = None
    current_company: Optional[str] = None
    current_location: Optional[str] = None
    total_experience_years: Optional[float] = None
    domain: Optional[DomainCategory] = None
    education_level: Optional[str] = None
    notice_period: Optional[str] = None
    skills: Optional[List[str]] = None
    source: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    resumes: List[ResumeOut] = []

    class Config:
        from_attributes = True
