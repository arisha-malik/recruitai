import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User, UserRole
from app.models.job import Job, JobStatus
from app.models.assistant import GeneratedJobDescription, GeneratedInterviewQuestion
from app.schemas.assistant import (
    JDGenerateRequest,
    JDGenerateResponse,
    InterviewQuestionsRequest,
    InterviewQuestionsResponse,
    JDRawParseRequest,
    JDRawParseResponse
)
from app.services.assistant_service import AssistantService, AssistantServiceError
from app.services.event_service import log_recruitment_event
from app.dependencies import get_current_user, RoleChecker

router = APIRouter(prefix="/assistant", tags=["AI Assistant"])

@router.post(
    "/parse-raw-jd",
    response_model=JDRawParseResponse,
    dependencies=[Depends(RoleChecker([UserRole.ADMIN, UserRole.RECRUITER, UserRole.HIRING_MANAGER]))]
)
def parse_raw_job_description(
    request: JDRawParseRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Parse a raw unstructured job description into structured form fields using the Gemini API.
    """
    service = AssistantService()
    try:
        data = service.parse_raw_job_description(request.text)
        
        # Log recruitment event
        log_recruitment_event(
            db=db,
            event_type="RAW_JD_PARSED",
            actor_id=current_user.id,
            metadata={"title_extracted": data.get("title")}
        )
        
        return {
            "status": "success",
            "data": data
        }
    except Exception as e:
        log_recruitment_event(
            db=db,
            event_type="RAW_JD_PARSING_FAILED",
            actor_id=current_user.id,
            metadata={"error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse raw JD: {str(e)}"
        )

@router.post(
    "/generate-jd",
    response_model=JDGenerateResponse,
    dependencies=[Depends(RoleChecker([UserRole.ADMIN, UserRole.RECRUITER, UserRole.HIRING_MANAGER]))]
)
def generate_job_description(
    request: JDGenerateRequest,
    save_to_job: bool = Query(False, description="Save generated JD as a new Job record"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate a professional Job Description using the Gemini API.
    Optionally saves the JD to the jobs table.
    """
    service = AssistantService()
    input_dict = request.model_dump()
    
    try:
        data = service.generate_job_description(db, input_dict)
        generated_jd_id = str(uuid.uuid4())
        job_id = None
        
        # Save to jobs table if save_to_job=True
        if save_to_job:
            db_job = Job(
                id=str(uuid.uuid4()),
                title=data["job_title"],
                department=data["department"],
                location=data["location"],
                employment_type=data["employment_type"],
                experience_level=data["experience_level"],
                description=data["full_job_description"],
                required_skills=data["required_skills"],
                status=JobStatus.DRAFT,
                created_by_id=current_user.id
            )
            db.add(db_job)
            db.commit()
            db.refresh(db_job)
            job_id = db_job.id
            
        # Save to generated outputs table
        db_jd_out = GeneratedJobDescription(
            id=generated_jd_id,
            created_by_id=current_user.id,
            job_id=job_id,
            input_json=input_dict,
            generated_json=data
        )
        db.add(db_jd_out)
        db.commit()
        
        # Log recruitment event
        log_recruitment_event(
            db=db,
            event_type="JD_GENERATED",
            job_id=job_id,
            actor_id=current_user.id,
            metadata={"generated_jd_id": generated_jd_id, "role": request.role}
        )
        
        return {
            "status": "success",
            "generated_jd_id": generated_jd_id,
            "job_id": job_id,
            "data": data
        }
        
    except Exception as e:
        db.rollback()
        # Log recruitment event failure
        log_recruitment_event(
            db=db,
            event_type="JD_GENERATION_FAILED",
            actor_id=current_user.id,
            metadata={"error": str(e), "role": request.role}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Job description generation failed: {str(e)}"
        )

@router.post(
    "/interview-questions",
    response_model=InterviewQuestionsResponse,
    dependencies=[Depends(RoleChecker([UserRole.ADMIN, UserRole.RECRUITER, UserRole.HIRING_MANAGER, UserRole.INTERVIEWER]))]
)
def generate_interview_questions(
    request: InterviewQuestionsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate relevant interview questions using the Gemini API.
    Can be personalized if candidate_id or job_id are provided.
    """
    service = AssistantService()
    input_dict = request.model_dump()
    
    try:
        data = service.generate_interview_questions(db, input_dict)
        generated_questions_id = str(uuid.uuid4())
        
        # Save to generated outputs table
        db_questions_out = GeneratedInterviewQuestion(
            id=generated_questions_id,
            created_by_id=current_user.id,
            candidate_id=request.candidate_id,
            job_id=request.job_id,
            type=request.round_type.upper(),
            level=request.difficulty.upper(),
            skills=[request.topic_or_skill],
            generated_json=data
        )
        db.add(db_questions_out)
        db.commit()
        
        # Log recruitment event
        log_recruitment_event(
            db=db,
            event_type="INTERVIEW_QUESTIONS_GENERATED",
            candidate_id=request.candidate_id,
            job_id=request.job_id,
            actor_id=current_user.id,
            metadata={"generated_questions_id": generated_questions_id, "type": request.round_type}
        )
        
        return {
            "status": "success",
            "generated_questions_id": generated_questions_id,
            "data": data
        }
        
    except Exception as e:
        db.rollback()
        # Log recruitment event failure
        log_recruitment_event(
            db=db,
            event_type="INTERVIEW_QUESTIONS_FAILED",
            candidate_id=request.candidate_id,
            job_id=request.job_id,
            actor_id=current_user.id,
            metadata={"error": str(e), "type": request.round_type if hasattr(request, 'round_type') else "UNKNOWN"}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Interview question generation failed: {str(e)}"
        )
