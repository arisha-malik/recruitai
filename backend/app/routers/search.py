from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, cast, String, func
from pydantic import BaseModel

from app.database import get_db
from app.models.user import UserRole
from app.models.candidate import Candidate, ParsedResumeData, Resume
from app.schemas.candidate import CandidateOut
from app.dependencies import RoleChecker
from app.services.llm_service import LLMService

router = APIRouter(prefix="/search", tags=["Search"])

class SearchResultOut(BaseModel):
    filters_applied: Dict[str, Any]
    candidates: List[CandidateOut]

@router.get(
    "/candidates",
    response_model=SearchResultOut,
    dependencies=[Depends(RoleChecker([UserRole.ADMIN, UserRole.RECRUITER, UserRole.HIRING_MANAGER]))]
)
def search_candidates(
    q: str = Query(..., description="Natural language search query"),
    db: Session = Depends(get_db)
):
    if not q.strip():
        return {"filters_applied": {}, "candidates": []}

    llm_service = LLMService()
    filters = llm_service.parse_search_query(q)

    query = db.query(Candidate).join(Resume, Resume.candidate_id == Candidate.id).join(ParsedResumeData, ParsedResumeData.resume_id == Resume.id)

    # Apply filters
    skills = filters.get("skills", [])
    if skills:
        # Check if skills exist in Candidate.skills (json) or ParsedResumeData.technical_skills
        for skill in skills:
            query = query.filter(
                or_(
                    cast(Candidate.skills, String).ilike(f"%{skill}%"),
                    cast(ParsedResumeData.technical_skills, String).ilike(f"%{skill}%")
                )
            )

    roles = filters.get("roles", [])
    if roles:
        role_conditions = []
        for role in roles:
            role_conditions.append(cast(ParsedResumeData.work_experience, String).ilike(f"%{role}%"))
            role_conditions.append(cast(ParsedResumeData.current_company, String).ilike(f"%{role}%"))
        if role_conditions:
            query = query.filter(or_(*role_conditions))

    locations = filters.get("locations", [])
    if locations:
        loc_conditions = []
        for loc in locations:
            loc_conditions.append(Candidate.current_location.ilike(f"%{loc}%"))
            loc_conditions.append(ParsedResumeData.current_location.ilike(f"%{loc}%"))
        if loc_conditions:
            query = query.filter(or_(*loc_conditions))

    min_exp = filters.get("min_experience_years")
    if min_exp is not None:
        try:
            exp_val = float(min_exp)
            query = query.filter(
                or_(
                    Candidate.total_experience_years >= exp_val,
                    ParsedResumeData.total_experience_years >= exp_val
                )
            )
        except ValueError:
            pass

    notice_period = filters.get("notice_period")
    if notice_period:
        query = query.filter(ParsedResumeData.notice_period.ilike(f"%{notice_period}%"))

    education = filters.get("education")
    if education:
        query = query.filter(cast(ParsedResumeData.education, String).ilike(f"%{education}%"))
        
    certifications = filters.get("certifications", [])
    if certifications:
        cert_conditions = []
        for cert in certifications:
            cert_conditions.append(cast(ParsedResumeData.certifications, String).ilike(f"%{cert}%"))
        if cert_conditions:
            query = query.filter(or_(*cert_conditions))

    # Distinct candidates only (since multiple resumes might match)
    candidates = query.distinct(Candidate.id).all()

    return {
        "filters_applied": filters,
        "candidates": candidates
    }
