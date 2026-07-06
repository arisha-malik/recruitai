from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import UserRole
from app.schemas.interview import (
    InterviewGuideRequest,
    InterviewGuideOut,
    JDGenerateRequest,
    JDGenerateOut
)
from app.services.interview_service import InterviewService
from app.dependencies import RoleChecker

router = APIRouter(prefix="/interview", tags=["Interview Assistant"])

@router.post(
    "/questions",
    response_model=InterviewGuideOut,
    dependencies=[Depends(RoleChecker([UserRole.ADMIN, UserRole.RECRUITER, UserRole.HIRING_MANAGER, UserRole.INTERVIEWER]))]
)
def generate_interview_questions(
    request: InterviewGuideRequest,
    db: Session = Depends(get_db)
):
    """
    Generates a structured list of interview questions tailored to a specific candidate, job role, and/or skill.
    Uses the configured LLM provider and relevant PromptTemplate.
    """
    service = InterviewService()
    try:
        res = service.generate_interview_guide(
            db=db,
            template_type=request.template_type,
            candidate_id=request.candidate_id,
            job_id=request.job_id,
            skill=request.skill,
            level=request.level
        )
        return res
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Interview guide generation failed: {str(e)}"
        )

@router.post(
    "/generate-jd",
    response_model=JDGenerateOut,
    dependencies=[Depends(RoleChecker([UserRole.ADMIN, UserRole.RECRUITER, UserRole.HIRING_MANAGER]))]
)
def generate_job_description(
    request: JDGenerateRequest,
    db: Session = Depends(get_db)
):
    """
    Generates a comprehensive and professional Job Description document in Markdown.
    Uses metadata input and the JD_GENERATOR PromptTemplate.
    """
    service = InterviewService()
    try:
        res = service.generate_job_description(
            db=db,
            title=request.title,
            department=request.department,
            location=request.location,
            experience_level=request.experience_level,
            employment_type=request.employment_type,
            key_skills=request.key_skills,
            additional_requirements=request.additional_requirements
        )
        return res
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Job description generation failed: {str(e)}"
        )
