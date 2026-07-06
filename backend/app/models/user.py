import enum
from sqlalchemy import Column, String, Enum, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    RECRUITER = "RECRUITER"
    HIRING_MANAGER = "HIRING_MANAGER"
    INTERVIEWER = "INTERVIEWER"

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.RECRUITER, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    # Relationships
    jobs = relationship("Job", back_populates="created_by", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="actor")
    recruitment_events = relationship("RecruitmentEvent", back_populates="actor")
