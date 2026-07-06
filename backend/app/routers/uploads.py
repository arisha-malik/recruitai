import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import UserRole
from app.models.candidate import Candidate, Resume, ParsingStatus
from app.services.s3_service import generate_presigned_post
from app.dependencies import RoleChecker

router = APIRouter(prefix="/uploads", tags=["Uploads"])

from typing import Optional
class PresignedUrlRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    file_name: str
    file_type: str

class PresignedUrlResponse(BaseModel):
    resume_id: str
    candidate_id: str
    upload_url: str
    fields: dict
    is_mock: bool

@router.post(
    "/presigned-url", 
    response_model=PresignedUrlResponse,
    dependencies=[Depends(RoleChecker([UserRole.ADMIN, UserRole.RECRUITER]))]
)
def get_upload_url(
    req: PresignedUrlRequest, 
    db: Session = Depends(get_db)
):
    # 1. Handle Anonymous vs Identified candidate
    if req.email:
        candidate = db.query(Candidate).filter(Candidate.email == req.email).first()
        if not candidate:
            candidate = Candidate(
                id=str(uuid.uuid4()),
                first_name=req.first_name or "Unknown",
                last_name=req.last_name or "Candidate",
                email=req.email,
                skills=[],
                source="DIRECT_UPLOAD"
            )
            db.add(candidate)
            db.commit()
            db.refresh(candidate)
    else:
        # Anonymous upload: Generate a placeholder candidate
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

    # 2. Create Resume database entry
    resume_id = str(uuid.uuid4())
    s3_key = f"resumes/{resume_id}/{req.file_name}"
    
    # Defaults bucket name
    bucket_name = os.getenv("AWS_S3_BUCKET", "recruitai-resumes")
    
    db_resume = Resume(
        id=resume_id,
        candidate_id=candidate.id,
        file_name=req.file_name,
        s3_key=s3_key,
        s3_bucket=bucket_name,
        parsing_status=ParsingStatus.UPLOADED
    )
    db.add(db_resume)
    db.commit()

    # 3. Generate presigned post fields
    presigned_data = generate_presigned_post(s3_key, req.file_type)
    
    return {
        "resume_id": resume_id,
        "candidate_id": candidate.id,
        "upload_url": presigned_data["upload_url"],
        "fields": presigned_data["fields"],
        "is_mock": presigned_data["is_mock"]
    }

@router.post("/mock-s3-upload", status_code=status.HTTP_201_CREATED)
def mock_s3_upload(
    key: str = Form(...),
    file: UploadFile = File(...)
):
    """
    Simulates direct-to-S3 upload for local development.
    Saves the file in backend/uploads/<s3_key> directory.
    """
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "uploads"))
    dest_path = os.path.join(base_dir, key)
    
    # Ensure nested folders exist
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    
    # Save the file to disk
    try:
        with open(dest_path, "wb") as f:
            f.write(file.file.read())
        return {
            "message": "Mock S3 upload successful",
            "s3_key": key,
            "filename": file.filename,
            "path": dest_path
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to write mock upload: {str(e)}"
        )
