from typing import List, Optional
from pydantic import BaseModel

class JDGenerateRequest(BaseModel):
    role: str
    department: str
    experience_level: str
    required_skills: List[str]
    nice_to_have_skills: List[str]
    location: str
    employment_type: str  # FULL_TIME | PART_TIME | CONTRACT | INTERNSHIP
    work_mode: str        # ONSITE | HYBRID | REMOTE
    responsibilities_hint: Optional[str] = None

class JDDataOut(BaseModel):
    job_title: str
    department: str
    location: str
    employment_type: str
    work_mode: str
    experience_level: str
    summary: str
    responsibilities: List[str]
    required_skills: List[str]
    nice_to_have_skills: List[str]
    qualifications: List[str]
    benefits: List[str]
    full_job_description: str

class JDGenerateResponse(BaseModel):
    status: str = "success"
    generated_jd_id: str
    job_id: Optional[str] = None
    data: JDDataOut

class InterviewQuestionsRequest(BaseModel):
    round_id: Optional[str] = None
    candidate_id: Optional[str] = None
    job_id: Optional[str] = None
    round_type: str         # technical | hr | managerial | assessment
    topic_or_skill: str
    difficulty: str         # beginner | intermediate | advanced
    count: int = 5

class QuestionItemOut(BaseModel):
    question: str
    expected_answer_points: List[str]
    difficulty: str         
    reason_for_asking: str
    round_type: Optional[str] = None
    topic: Optional[str] = None

class InterviewQuestionsDataOut(BaseModel):
    round_type: str
    difficulty: str
    topic: str
    questions: List[QuestionItemOut]

class InterviewQuestionsResponse(BaseModel):
    status: str = "success"
    generated_questions_id: str
    data: InterviewQuestionsDataOut

class JDRawParseRequest(BaseModel):
    text: str

class JDRawParseDataOut(BaseModel):
    title: str
    department: str
    location: str
    employment_type: str
    experience_level: str
    description: str
    required_skills: List[str]

class JDRawParseResponse(BaseModel):
    status: str = "success"
    data: JDRawParseDataOut
