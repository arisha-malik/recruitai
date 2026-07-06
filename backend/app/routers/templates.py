import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import UserRole
from app.models.application import PromptTemplate, TemplateType
from app.schemas.template import PromptTemplateCreate, PromptTemplateUpdate, PromptTemplateOut
from app.dependencies import RoleChecker

router = APIRouter(prefix="/templates", tags=["Prompt Templates"])

# Default prompt templates to seed
DEFAULT_TEMPLATES = [
    {
        "skill": "General",
        "level": "Mid",
        "type": TemplateType.TECHNICAL,
        "template_text": (
            "You are a senior technical interviewer. Generate a technical interview guide for a {level} level {skill} candidate.\n\n"
            "Candidate Profile details:\n{candidate_details}\n\n"
            "Job Description details:\n{job_details}\n\n"
            "Generate 5 challenging technical questions testing their hands-on skills, along with expected answer points, specific evaluation criteria, and difficulty level (EASY, MEDIUM, HARD). Make sure the questions are tailored to their background if the candidate profile is provided.\n\n"
            "Return ONLY a JSON object matching the schema below. Do NOT wrap in markdown code blocks. Do NOT include any introductory or trailing text.\n\n"
            "JSON Schema:\n"
            "{{\n"
            "  \"role\": \"{skill}\",\n"
            "  \"experience_level\": \"{level}\",\n"
            "  \"template_type\": \"TECHNICAL\",\n"
            "  \"questions\": [\n"
            "    {{\n"
            "      \"question\": \"string\",\n"
            "      \"expected_answer_points\": [\"string\"],\n"
            "      \"evaluation_criteria\": \"string\",\n"
            "      \"difficulty\": \"EASY | MEDIUM | HARD\"\n"
            "    }}\n"
            "  ]\n"
            "}}"
        )
    },
    {
        "skill": "General",
        "level": "Mid",
        "type": TemplateType.HR,
        "template_text": (
            "You are a senior HR manager. Generate a behavioral and cultural fit interview guide for a {level} level {skill} candidate.\n\n"
            "Candidate Profile details:\n{candidate_details}\n\n"
            "Job Description details:\n{job_details}\n\n"
            "Generate 5 questions focusing on situational analysis, teamwork, conflict resolution, work ethic, and adaptability. Provide expected answers and evaluation criteria.\n\n"
            "Return ONLY a JSON object matching the schema below. Do NOT wrap in markdown code blocks. Do NOT include any introductory or trailing text.\n\n"
            "JSON Schema:\n"
            "{{\n"
            "  \"role\": \"{skill}\",\n"
            "  \"experience_level\": \"{level}\",\n"
            "  \"template_type\": \"HR\",\n"
            "  \"questions\": [\n"
            "    {{\n"
            "      \"question\": \"string\",\n"
            "      \"expected_answer_points\": [\"string\"],\n"
            "      \"evaluation_criteria\": \"string\",\n"
            "      \"difficulty\": \"EASY | MEDIUM | HARD\"\n"
            "    }}\n"
            "  ]\n"
            "}}"
        )
    },
    {
        "skill": "General",
        "level": "Mid",
        "type": TemplateType.MANAGERIAL,
        "template_text": (
            "You are a senior hiring manager. Generate a managerial and leadership interview guide for a {level} level {skill} candidate.\n\n"
            "Candidate Profile details:\n{candidate_details}\n\n"
            "Job Description details:\n{job_details}\n\n"
            "Generate 5 questions testing leadership, project management, system architectural decisions, and communication. Provide expected answer points and evaluation criteria.\n\n"
            "Return ONLY a JSON object matching the schema below. Do NOT wrap in markdown code blocks. Do NOT include any introductory or trailing text.\n\n"
            "JSON Schema:\n"
            "{{\n"
            "  \"role\": \"{skill}\",\n"
            "  \"experience_level\": \"{level}\",\n"
            "  \"template_type\": \"MANAGERIAL\",\n"
            "  \"questions\": [\n"
            "    {{\n"
            "      \"question\": \"string\",\n"
            "      \"expected_answer_points\": [\"string\"],\n"
            "      \"evaluation_criteria\": \"string\",\n"
            "      \"difficulty\": \"EASY | MEDIUM | HARD\"\n"
            "    }}\n"
            "  ]\n"
            "}}"
        )
    },
    {
        "skill": "General",
        "level": "Mid",
        "type": TemplateType.JD_GENERATOR,
        "template_text": (
            "You are an expert technical recruiter and writer. Generate a comprehensive, professional job description in Markdown format based on the following role metadata:\n\n"
            "Role Title: {title}\n"
            "Department: {department}\n"
            "Location: {location}\n"
            "Experience Level Required: {experience_level}\n"
            "Employment Type: {employment_type}\n"
            "Key Required Skills: {key_skills}\n"
            "Additional Requirements/Context: {additional_requirements}\n\n"
            "Your generated job description should include: Role Overview, Key Responsibilities, Required Technical Skills, Preferred Qualifications, and Benefits/About the Company.\n\n"
            "Return ONLY a JSON object matching the schema below. Do NOT wrap in markdown code blocks. Do NOT include any introductory or trailing text.\n\n"
            "JSON Schema:\n"
            "{{\n"
            "  \"title\": \"string\",\n"
            "  \"department\": \"string\",\n"
            "  \"description\": \"string\",\n"
            "  \"required_skills\": [\"string\"]\n"
            "}}"
        )
    }
]

@router.get(
    "/",
    response_model=List[PromptTemplateOut],
    dependencies=[Depends(RoleChecker([UserRole.ADMIN, UserRole.RECRUITER, UserRole.HIRING_MANAGER, UserRole.INTERVIEWER]))]
)
def list_templates(
    type: Optional[TemplateType] = Query(None, description="Filter by template type"),
    skill: Optional[str] = Query(None, description="Filter by skill"),
    level: Optional[str] = Query(None, description="Filter by level"),
    db: Session = Depends(get_db)
):
    query = db.query(PromptTemplate)
    if type:
        query = query.filter(PromptTemplate.type == type)
    if skill:
        query = query.filter(PromptTemplate.skill.ilike(f"%{skill}%"))
    if level:
        query = query.filter(PromptTemplate.level.ilike(f"%{level}%"))
    return query.all()

@router.get(
    "/{template_id}",
    response_model=PromptTemplateOut,
    dependencies=[Depends(RoleChecker([UserRole.ADMIN, UserRole.RECRUITER, UserRole.HIRING_MANAGER, UserRole.INTERVIEWER]))]
)
def get_template(template_id: str, db: Session = Depends(get_db)):
    tpl = db.query(PromptTemplate).filter(PromptTemplate.id == template_id).first()
    if not tpl:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prompt template not found."
        )
    return tpl

@router.post(
    "/",
    response_model=PromptTemplateOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RoleChecker([UserRole.ADMIN, UserRole.RECRUITER]))]
)
def create_template(tpl_in: PromptTemplateCreate, db: Session = Depends(get_db)):
    db_tpl = PromptTemplate(
        id=str(uuid.uuid4()),
        skill=tpl_in.skill,
        level=tpl_in.level,
        type=tpl_in.type,
        template_text=tpl_in.template_text
    )
    db.add(db_tpl)
    db.commit()
    db.refresh(db_tpl)
    return db_tpl

@router.put(
    "/{template_id}",
    response_model=PromptTemplateOut,
    dependencies=[Depends(RoleChecker([UserRole.ADMIN, UserRole.RECRUITER]))]
)
def update_template(
    template_id: str,
    tpl_in: PromptTemplateUpdate,
    db: Session = Depends(get_db)
):
    tpl = db.query(PromptTemplate).filter(PromptTemplate.id == template_id).first()
    if not tpl:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prompt template not found."
        )
        
    update_data = tpl_in.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(tpl, field, val)
        
    db.commit()
    db.refresh(tpl)
    return tpl

@router.delete(
    "/{template_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(RoleChecker([UserRole.ADMIN]))]
)
def delete_template(template_id: str, db: Session = Depends(get_db)):
    tpl = db.query(PromptTemplate).filter(PromptTemplate.id == template_id).first()
    if not tpl:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prompt template not found."
        )
    db.delete(tpl)
    db.commit()
    return None

@router.post(
    "/seed",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(RoleChecker([UserRole.ADMIN, UserRole.RECRUITER]))]
)
def seed_templates(db: Session = Depends(get_db)):
    """
    Populate default templates if they are missing.
    """
    created_count = 0
    for defaults in DEFAULT_TEMPLATES:
        # Check if equivalent template already exists
        existing = db.query(PromptTemplate).filter(
            PromptTemplate.skill == defaults["skill"],
            PromptTemplate.level == defaults["level"],
            PromptTemplate.type == defaults["type"]
        ).first()
        
        if not existing:
            db_tpl = PromptTemplate(
                id=str(uuid.uuid4()),
                skill=defaults["skill"],
                level=defaults["level"],
                type=defaults["type"],
                template_text=defaults["template_text"]
            )
            db.add(db_tpl)
            created_count += 1
            
    if created_count > 0:
        db.commit()
        
    return {
        "success": True,
        "message": f"Successfully seeded {created_count} default templates.",
        "seeded_count": created_count
    }
