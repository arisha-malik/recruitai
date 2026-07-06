import uuid
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.audit import RecruitmentEvent, AuditLog

def log_recruitment_event(
    db: Session,
    event_type: str,
    candidate_id: Optional[str] = None,
    resume_id: Optional[str] = None,
    job_id: Optional[str] = None,
    application_id: Optional[str] = None,
    actor_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> RecruitmentEvent:
    """
    Utility function to write a recruitment pipeline event log to PostgreSQL.
    """
    event = RecruitmentEvent(
        id=str(uuid.uuid4()),
        event_type=event_type,
        candidate_id=candidate_id,
        resume_id=resume_id,
        job_id=job_id,
        application_id=application_id,
        actor_id=actor_id,
        metadata_json=metadata or {}
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event

def log_audit_action(
    db: Session,
    action: str,
    table_name: str,
    record_id: str,
    actor_id: Optional[str] = None,
    old_values: Optional[Dict[str, Any]] = None,
    new_values: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None
) -> AuditLog:
    """
    Utility function to write a sensitive database audit record.
    """
    audit = AuditLog(
        id=str(uuid.uuid4()),
        action=action,
        table_name=table_name,
        record_id=record_id,
        actor_id=actor_id,
        old_values=old_values,
        new_values=new_values,
        ip_address=ip_address
    )
    db.add(audit)
    db.commit()
    db.refresh(audit)
    return audit
