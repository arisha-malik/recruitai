from typing import List, Optional
from pydantic import BaseModel

class MatchRunResponse(BaseModel):
    matching_job_id: str
    job_id: str
    status: str

class MatchStatusResponse(BaseModel):
    job_id: str
    status: str
    total_candidates_checked: int
    total_matches_created: int
    error_message: Optional[str] = None

class CandidateMatchResultOut(BaseModel):
    candidate_id: str
    application_id: Optional[str] = None
    candidate_name: str
    match_percentage: float
    skill_match_analysis: str
    matched_skills: List[str]
    missing_skills: List[str]
    experience_analysis: Optional[str] = None
    experience_delta: str
    location_fit: str
    notice_period_fit: str
    strengths: List[str]
    concerns: List[str]
    final_recommendation: str
    summary: Optional[str] = None

class MatchResultsResponse(BaseModel):
    job_id: str
    results: List[CandidateMatchResultOut]
