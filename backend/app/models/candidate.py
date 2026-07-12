import enum
from sqlalchemy import Column, String, Float, Enum, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class ParsingStatus(str, enum.Enum):
    UPLOADED = "UPLOADED"
    PARSING = "PARSING"
    PARSED = "PARSED"
    FAILED = "FAILED"

class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(String, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, nullable=True)
    current_company = Column(String, nullable=True)
    current_location = Column(String, nullable=True, index=True)
    total_experience_years = Column(Float, nullable=True, index=True)
    domain = Column(String, nullable=True, index=True)
    education_level = Column(String, nullable=True)
    notice_period = Column(String, nullable=True)
    skills = Column(JSON, nullable=True)  # List of skills: ["Python", "FastAPI"]
    source = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    # Relationships
    resumes = relationship("Resume", back_populates="candidate", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="candidate", cascade="all, delete-orphan")
    match_results = relationship("MatchResult", back_populates="candidate", cascade="all, delete-orphan")
    recruitment_events = relationship("RecruitmentEvent", back_populates="candidate")

class Resume(Base):
    __tablename__ = "resumes"

    id = Column(String, primary_key=True, index=True)
    candidate_id = Column(String, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False)
    file_name = Column(String, nullable=False)
    original_filename = Column(String, nullable=True)
    stored_filename = Column(String, nullable=True)
    storage_path = Column(String, nullable=True)
    candidate_primary_designation = Column(String, nullable=True)
    primary_skill = Column(String, nullable=True)
    candidate_field = Column(String, nullable=True)
    searchable_storage_label = Column(String, nullable=True)
    s3_key = Column(String, nullable=False)
    s3_bucket = Column(String, nullable=False)
    parsing_status = Column(Enum(ParsingStatus), default=ParsingStatus.UPLOADED, nullable=False, index=True)
    raw_text = Column(Text, nullable=True)
    failure_reason = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    # Relationships
    candidate = relationship("Candidate", back_populates="resumes")
    parsed_data = relationship("ParsedResumeData", uselist=False, back_populates="resume", cascade="all, delete-orphan")
    events = relationship("RecruitmentEvent", back_populates="resume")

class ParsedResumeData(Base):
    __tablename__ = "parsed_resume_data"

    id = Column(String, primary_key=True, index=True)
    resume_id = Column(String, ForeignKey("resumes.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    full_name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    mobile_number = Column(String, nullable=True)
    total_experience = Column(Float, nullable=True)
    total_experience_years = Column(Float, nullable=True)
    technical_skills = Column(JSON, nullable=True)  # List of skills
    education = Column(JSON, nullable=True)         # List of dicts
    certifications = Column(JSON, nullable=True)    # List of strings
    current_company = Column(String, nullable=True)
    current_location = Column(String, nullable=True)
    notice_period = Column(String, nullable=True)
    work_experience = Column(JSON, nullable=True)   # List of dicts
    projects = Column(JSON, nullable=True)          # List of dicts
    raw_json = Column(JSON, nullable=True)          # Raw LLM output
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    resume = relationship("Resume", back_populates="parsed_data")
