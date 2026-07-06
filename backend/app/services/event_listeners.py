import uuid
import logging
from sqlalchemy import event, inspect
from sqlalchemy.orm import object_session
from app.models.application import Application
from app.models.candidate import Candidate, Resume
from app.models.job import Job
from app.models.audit import RecruitmentEvent

logger = logging.getLogger(__name__)

def register_event_listeners():
    """
    Registers transparent database event listeners to intercept mutations
    on candidate, resume, and application models and write event logs.
    """
    logger.info("Registering RecruitAI database event listeners...")

    @event.listens_for(Candidate, "after_insert")
    def candidate_after_insert(mapper, connection, target):
        session = object_session(target)
        actor_id = session.info.get("current_user_id") if session else None
        connection.execute(
            RecruitmentEvent.__table__.insert().values(
                id=str(uuid.uuid4()),
                event_type="CANDIDATE_CREATED",
                candidate_id=target.id,
                resume_id=None,
                job_id=None,
                application_id=None,
                actor_id=actor_id,
                metadata_json={"email": target.email, "name": f"{target.first_name} {target.last_name}"}
            )
        )

    @event.listens_for(Resume, "after_insert")
    def resume_after_insert(mapper, connection, target):
        session = object_session(target)
        actor_id = session.info.get("current_user_id") if session else None
        connection.execute(
            RecruitmentEvent.__table__.insert().values(
                id=str(uuid.uuid4()),
                event_type="RESUME_UPLOADED",
                candidate_id=target.candidate_id,
                resume_id=target.id,
                job_id=None,
                application_id=None,
                actor_id=actor_id,
                metadata_json={"file_name": target.file_name}
            )
        )

    @event.listens_for(Job, "after_insert")
    def job_after_insert(mapper, connection, target):
        connection.execute(
            RecruitmentEvent.__table__.insert().values(
                id=str(uuid.uuid4()),
                event_type="JOB_CREATED",
                candidate_id=None,
                resume_id=None,
                job_id=target.id,
                application_id=None,
                actor_id=target.created_by_id,
                metadata_json={"title": target.title}
            )
        )

    @event.listens_for(Application, "after_insert")
    def application_after_insert(mapper, connection, target):
        status_val = target.status.value if hasattr(target.status, "value") else str(target.status)
        session = object_session(target)
        actor_id = session.info.get("current_user_id") if session else None
        connection.execute(
            RecruitmentEvent.__table__.insert().values(
                id=str(uuid.uuid4()),
                event_type="CANDIDATE_CREATED" if False else "APPLICATION_CREATED", # just keep it clean
                candidate_id=target.candidate_id,
                resume_id=None,
                job_id=target.job_id,
                application_id=target.id,
                actor_id=actor_id,
                metadata_json={"status": status_val}
            )
        )

    @event.listens_for(Application, "after_update")
    def application_after_update(mapper, connection, target):
        state = inspect(target)
        history = state.get_history("status", True)
        if history.has_changes():
            old_status = history.deleted[0] if history.deleted else None
            new_status = history.added[0] if history.added else target.status
            
            old_status_val = old_status.value if hasattr(old_status, "value") else str(old_status) if old_status else None
            new_status_val = new_status.value if hasattr(new_status, "value") else str(new_status)
            
            session = object_session(target)
            actor_id = session.info.get("current_user_id") if session else None
            
            # Log APPLICATION_STATUS_UPDATED for backward compatibility / tests
            connection.execute(
                RecruitmentEvent.__table__.insert().values(
                    id=str(uuid.uuid4()),
                    event_type="APPLICATION_STATUS_UPDATED",
                    candidate_id=target.candidate_id,
                    resume_id=None,
                    job_id=target.job_id,
                    application_id=target.id,
                    actor_id=actor_id,
                    metadata_json={
                        "old_status": old_status_val,
                        "new_status": new_status_val
                    }
                )
            )

            # Log APPLICATION_STATUS_CHANGED for Phase 5 consistency
            connection.execute(
                RecruitmentEvent.__table__.insert().values(
                    id=str(uuid.uuid4()),
                    event_type="APPLICATION_STATUS_CHANGED",
                    candidate_id=target.candidate_id,
                    resume_id=None,
                    job_id=target.job_id,
                    application_id=target.id,
                    actor_id=actor_id,
                    metadata_json={
                        "old_status": old_status_val,
                        "new_status": new_status_val
                    }
                )
            )
