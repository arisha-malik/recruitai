from sqlalchemy import Column, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class RecruitmentEvent(Base):
    __tablename__ = "recruitment_events"

    id = Column(String, primary_key=True, index=True)
    event_type = Column(String, nullable=False, index=True) # e.g. RESUME_UPLOADED, RESUME_PARSED
    candidate_id = Column(String, ForeignKey("candidates.id", ondelete="SET NULL"), nullable=True)
    resume_id = Column(String, ForeignKey("resumes.id", ondelete="SET NULL"), nullable=True)
    job_id = Column(String, ForeignKey("jobs.id", ondelete="SET NULL"), nullable=True)
    application_id = Column(String, ForeignKey("applications.id", ondelete="SET NULL"), nullable=True)
    actor_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    metadata_json = Column(JSON, nullable=True) # stores event metadata
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    candidate = relationship("Candidate", back_populates="recruitment_events")
    resume = relationship("Resume", back_populates="events")
    job = relationship("Job", back_populates="recruitment_events")
    application = relationship("Application", back_populates="recruitment_events")
    actor = relationship("User", back_populates="recruitment_events")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, index=True)
    action = Column(String, nullable=False)     # e.g., USER_LOGIN, DELETE_CANDIDATE
    table_name = Column(String, nullable=False)
    record_id = Column(String, nullable=False)
    actor_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    ip_address = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    actor = relationship("User", back_populates="audit_logs")
