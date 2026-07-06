from typing import List, Optional
from pydantic import BaseModel
from app.models.application import TemplateType

class InterviewGuideRequest(BaseModel):
    candidate_id: Optional[str] = None
    job_id: Optional[str] = None
    skill: Optional[str] = None
    level: Optional[str] = None
    template_type: TemplateType

class QuestionOut(BaseModel):
    question: str
    expected_answer_points: List[str]
    evaluation_criteria: str
    difficulty: str  # EASY, MEDIUM, HARD

class InterviewGuideOut(BaseModel):
    role: str
    experience_level: str
    template_type: TemplateType
    questions: List[QuestionOut]

class JDGenerateRequest(BaseModel):
    title: str
    department: str
    location: str
    experience_level: str  # e.g., Senior, Junior
    employment_type: str   # e.g., FULL_TIME, CONTRACT
    key_skills: List[str]
    additional_requirements: Optional[str] = None

class JDGenerateOut(BaseModel):
    title: str
    department: str
    description: str  # Markdown text
    required_skills: List[str]
