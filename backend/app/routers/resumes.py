from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import List
import uuid
import os

from app.config import settings
from app.database import get_db
from app.models.user import User, UserRole
from app.models.candidate import Resume, ParsingStatus, Candidate
from app.worker.tasks import parse_resume_job
from app.dependencies import get_current_user, RoleChecker
from app.services.s3_service import store_uploaded_file

router = APIRouter(prefix="/resumes", tags=["Resumes"])

class ParseResumeResponse(BaseModel):
    jobId: str
    resumeId: str
    status: ParsingStatus

class ResumeStatusResponse(BaseModel):
    resumeId: str
    status: ParsingStatus
    failure_reason: str | None = None

class BulkUploadResponseItem(BaseModel):
    filename: str
    resume_id: str | None = None
    status: str
    error: str | None = None

class BulkUploadResponse(BaseModel):
    results: List[BulkUploadResponseItem]

@router.post(
    "/bulk-upload",
    response_model=BulkUploadResponse,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(RoleChecker([UserRole.ADMIN, UserRole.RECRUITER]))]
)
def bulk_upload_resumes(
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    results = []
    bucket_name = os.getenv("AWS_S3_BUCKET", "recruitai-resumes")
    allowed_extensions = [".pdf", ".doc", ".docx"]

    for file in files:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in allowed_extensions:
            results.append(BulkUploadResponseItem(
                filename=file.filename,
                status="FAILED",
                error=f"Invalid file type {ext}. Supported: PDF, DOC, DOCX"
            ))
            continue

        placeholder_uuid = str(uuid.uuid4())
        candidate = Candidate(
            id=placeholder_uuid,
            first_name="Pending",
            last_name="Parsing",
            email=f"pending-{placeholder_uuid}@recruitai.com",
            skills=[],
            source="DIRECT_UPLOAD"
        )
        db.add(candidate)
        
        resume_id = str(uuid.uuid4())
        s3_key = f"{settings.S3_PREFIX}Resume/tmp/{resume_id}_{file.filename}"
        
        db_resume = Resume(
            id=resume_id,
            candidate_id=candidate.id,
            file_name=file.filename,
            s3_key=s3_key,
            s3_bucket=bucket_name,
            parsing_status=ParsingStatus.UPLOADED
        )
        db.add(db_resume)

        try:
            store_uploaded_file(file, s3_key)
            db.commit()
        except Exception as e:
            db.rollback()
            results.append(BulkUploadResponseItem(
                filename=file.filename,
                status="FAILED",
                error=f"Failed to store file: {str(e)}"
            ))
            continue
            
        # Trigger parsing
        db_resume.parsing_status = ParsingStatus.PARSING
        db.commit()
        
        if settings.RUN_JOBS_SYNC:
            parse_resume_job.apply(args=(resume_id, current_user.id))
        else:
            parse_resume_job.delay(resume_id, current_user.id)
            
        results.append(BulkUploadResponseItem(
            filename=file.filename,
            resume_id=resume_id,
            status="PARSING"
        ))
        
    return BulkUploadResponse(results=results)

@router.post(
    "/upload",
    response_model=ParseResumeResponse,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(RoleChecker([UserRole.ADMIN, UserRole.RECRUITER]))]
)
def upload_single_resume(
    file: UploadFile = File(...),
    first_name: str | None = Form(None),
    last_name: str | None = Form(None),
    email: EmailStr | None = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    bucket_name = os.getenv("AWS_S3_BUCKET", "recruitai-resumes")
    allowed_extensions = [".pdf", ".doc", ".docx"]
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"Invalid file type {ext}. Supported: PDF, DOC, DOCX")

    # 1. Handle Candidate
    if email:
        candidate = db.query(Candidate).filter(Candidate.email == email).first()
        if not candidate:
            candidate = Candidate(
                id=str(uuid.uuid4()),
                first_name=first_name or "Unknown",
                last_name=last_name or "Candidate",
                email=email,
                skills=[],
                source="DIRECT_UPLOAD"
            )
            db.add(candidate)
            db.commit()
            db.refresh(candidate)
    else:
        placeholder_uuid = str(uuid.uuid4())
        candidate = Candidate(
            id=placeholder_uuid,
            first_name="Pending",
            last_name="Parsing",
            email=f"pending-{placeholder_uuid}@recruitai.com",
            skills=[],
            source="DIRECT_UPLOAD"
        )
        db.add(candidate)
        db.commit()
        db.refresh(candidate)

    # 2. Create Resume
    resume_id = str(uuid.uuid4())
    s3_key = f"{settings.S3_PREFIX}Resume/tmp/{resume_id}_{file.filename}"
    
    db_resume = Resume(
        id=resume_id,
        candidate_id=candidate.id,
        file_name=file.filename,
        original_filename=file.filename,
        s3_key=s3_key,
        s3_bucket=bucket_name,
        parsing_status=ParsingStatus.UPLOADED
    )
    db.add(db_resume)

    # 3. Store file and trigger parse
    try:
        store_uploaded_file(file, s3_key)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to store file: {str(e)}")

    db_resume.parsing_status = ParsingStatus.PARSING
    db.commit()

    if settings.RUN_JOBS_SYNC:
        task = parse_resume_job.apply(args=(resume_id, current_user.id))
    else:
        task = parse_resume_job.delay(resume_id, current_user.id)

    return {
        "jobId": str(task.id),
        "resumeId": resume_id,
        "status": ParsingStatus.PARSING
    }


@router.post(
    "/{resume_id}/parse", 
    response_model=ParseResumeResponse,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(RoleChecker([UserRole.ADMIN, UserRole.RECRUITER]))]
)
def parse_resume(
    resume_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Trigger the asynchronous resume parsing pipeline for an uploaded resume.
    Returns the background Celery jobId immediately without blocking.
    """
    # 1. Verify resume exists in database
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume record not found."
        )
        
    # 2. Update status to PARSING
    resume.parsing_status = ParsingStatus.PARSING
    db.commit()
    
    # 3. Enqueue the task (synchronously if configured for local testing)
    if settings.RUN_JOBS_SYNC:
        task = parse_resume_job.apply(args=(resume_id, current_user.id))
    else:
        task = parse_resume_job.delay(resume_id, current_user.id)
    
    return {
        "jobId": str(task.id),
        "resumeId": resume_id,
        "status": ParsingStatus.PARSING
    }

@router.get(
    "/{resume_id}/status", 
    response_model=ResumeStatusResponse,
    dependencies=[Depends(RoleChecker([UserRole.ADMIN, UserRole.RECRUITER, UserRole.HIRING_MANAGER]))]
)
def get_resume_status(
    resume_id: str,
    db: Session = Depends(get_db)
):
    """
    Get the current processing status of the resume parsing pipeline.
    """
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume record not found."
        )
        
    return {
        "resumeId": resume.id,
        "status": resume.parsing_status,
        "failure_reason": resume.failure_reason
    }
