import enum
from sqlalchemy import Column, String, Float, Enum, DateTime, ForeignKey, Text, JSON, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class ApplicationStatus(str, enum.Enum):
    APPLIED = "APPLIED"
    PARSING = "PARSING"
    MATCHED = "MATCHED"
    MAYBE = "MAYBE"
    SHORTLISTED = "SHORTLISTED"
    INTERVIEWING = "INTERVIEWING"
    OFFERED = "OFFERED"
    REJECTED = "REJECTED"

class TemplateType(str, enum.Enum):
    TECHNICAL = "TECHNICAL"
    HR = "HR"
    MANAGERIAL = "MANAGERIAL"
    JD_GENERATOR = "JD_GENERATOR"

class Application(Base):
    __tablename__ = "applications"

    id = Column(String, primary_key=True, index=True)
    candidate_id = Column(String, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False)
    job_id = Column(String, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(Enum(ApplicationStatus), default=ApplicationStatus.APPLIED, nullable=False, index=True)
    
    shortlisted_at = Column(DateTime(timezone=True), nullable=True)
    interviewing_at = Column(DateTime(timezone=True), nullable=True)
    offered_at = Column(DateTime(timezone=True), nullable=True)
    rejected_at = Column(DateTime(timezone=True), nullable=True)
    
    applied_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    # Relationships
    candidate = relationship("Candidate", back_populates="applications")
    job = relationship("Job", back_populates="applications")
    match_results = relationship("MatchResult", back_populates="application", cascade="all, delete-orphan")
    recruitment_events = relationship("RecruitmentEvent", back_populates="application")

class MatchResult(Base):
    __tablename__ = "match_results"

    id = Column(String, primary_key=True, index=True)
    candidate_id = Column(String, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False)
    job_id = Column(String, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    application_id = Column(String, ForeignKey("applications.id", ondelete="CASCADE"), nullable=True)
    
    vector_similarity_score = Column(Float, nullable=True)
    match_percentage = Column(Float, nullable=False, index=True)
    skill_match_analysis = Column(Text, nullable=False)
    matched_skills = Column(JSON, nullable=True)     # List of strings
    missing_skills = Column(JSON, nullable=True)     # List of strings
    experience_analysis = Column(Text, nullable=True)
    experience_delta = Column(String, nullable=False)  # string representation of exp delta
    location_fit = Column(String, nullable=False)
    notice_period_fit = Column(String, nullable=False)
    strengths = Column(JSON, nullable=True)           # List of strings
    concerns = Column(JSON, nullable=True)            # List of strings
    final_recommendation = Column(String, nullable=False)  # SHORTLIST, MAYBE, REJECT
    summary = Column(Text, nullable=True)
    raw_llm_response = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    # Ensure one match result per candidate per job
    __table_args__ = (
        UniqueConstraint('candidate_id', 'job_id', name='uq_candidate_job_match'),
    )

    # Relationships
    candidate = relationship("Candidate", back_populates="match_results")
    job = relationship("Job", back_populates="match_results")
    application = relationship("Application", back_populates="match_results")

class PromptTemplate(Base):
    __tablename__ = "prompt_templates"

    id = Column(String, primary_key=True, index=True)
    skill = Column(String, nullable=False)  # e.g., "Java", "Python", "General"
    level = Column(String, nullable=False)  # e.g., "Junior", "Mid", "Senior"
    type = Column(Enum(TemplateType), default=TemplateType.TECHNICAL, nullable=False)
    template_text = Column(Text, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
