from sqlalchemy import Column, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class GeneratedJobDescription(Base):
    __tablename__ = "generated_job_descriptions"

    id = Column(String, primary_key=True, index=True)
    created_by_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    job_id = Column(String, ForeignKey("jobs.id", ondelete="SET NULL"), nullable=True)
    input_json = Column(JSON, nullable=False)
    generated_json = Column(JSON, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    created_by = relationship("User")
    job = relationship("Job")

class GeneratedInterviewQuestion(Base):
    __tablename__ = "generated_interview_questions"

    id = Column(String, primary_key=True, index=True)
    created_by_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    candidate_id = Column(String, ForeignKey("candidates.id", ondelete="SET NULL"), nullable=True)
    job_id = Column(String, ForeignKey("jobs.id", ondelete="SET NULL"), nullable=True)
    
    type = Column(String, nullable=False)   # TECHNICAL, HR, MANAGERIAL
    level = Column(String, nullable=False)  # JUNIOR, MID, SENIOR
    skills = Column(JSON, nullable=False)   # List of skills
    generated_json = Column(JSON, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    created_by = relationship("User")
    candidate = relationship("Candidate")
    job = relationship("Job")
