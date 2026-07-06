import enum
from sqlalchemy import Column, String, Enum, DateTime, ForeignKey, JSON, Text, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
from app.models.domain import DomainCategory

class JobStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    OPEN = "OPEN"
    CLOSED = "CLOSED"

class JobEmbeddingStatus(str, enum.Enum):
    PENDING = "PENDING"
    EMBEDDING = "EMBEDDING"
    EMBEDDED = "EMBEDDED"
    FAILED = "FAILED"

class MatchingStatus(str, enum.Enum):
    PENDING = "PENDING"
    MATCHING = "MATCHING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class Job(Base):
    __tablename__ = "jobs"

    id = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=False)
    department = Column(String, nullable=True, index=True)
    domain = Column(String, default=DomainCategory.OTHER.value, nullable=False, index=True)
    location = Column(String, nullable=True)
    employment_type = Column(String, nullable=False)  # e.g., FULL_TIME, CONTRACT
    experience_level = Column(String, nullable=True) # e.g., Senior, Junior
    description = Column(Text, nullable=False)
    required_skills = Column(JSON, nullable=True)     # List of strings: ["Python", "FastAPI"]
    status = Column(Enum(JobStatus), default=JobStatus.DRAFT, nullable=False, index=True)
    created_by_id = Column(String, ForeignKey("users.id"), nullable=False)
    embedding_status = Column(Enum(JobEmbeddingStatus), default=JobEmbeddingStatus.PENDING, nullable=False)
    matching_status = Column(Enum(MatchingStatus), default=MatchingStatus.PENDING, nullable=False)
    matching_error = Column(Text, nullable=True)
    total_candidates_checked = Column(Integer, default=0, nullable=False)
    total_matches_created = Column(Integer, default=0, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    # Relationships
    created_by = relationship("User", back_populates="jobs")
    applications = relationship("Application", back_populates="job", cascade="all, delete-orphan")
    match_results = relationship("MatchResult", back_populates="job", cascade="all, delete-orphan")
    recruitment_events = relationship("RecruitmentEvent", back_populates="job")
