import json
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.config import settings
from app.models.application import PromptTemplate, TemplateType
from app.models.candidate import Candidate, ParsedResumeData
from app.models.job import Job

logger = logging.getLogger(__name__)

# Fallback default template texts in case DB is not seeded
FALLBACK_TECHNICAL_TEMPLATE = (
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

FALLBACK_HR_TEMPLATE = (
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

FALLBACK_MANAGERIAL_TEMPLATE = (
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

FALLBACK_JD_TEMPLATE = (
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

class InterviewServiceError(Exception):
    pass

class InterviewService:
    def __init__(self):
        self.provider = settings.LLM_PROVIDER.lower()
        self._init_provider()

    def _init_provider(self):
        if self.provider == "gemini":
            import google.generativeai as genai
            genai.configure(api_key=settings.GEMINI_API_KEY)
        elif self.provider == "openai":
            from openai import OpenAI
            self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        else:
            raise InterviewServiceError(f"Unsupported LLM provider: {self.provider}")

    def generate_interview_guide(
        self,
        db: Session,
        template_type: TemplateType,
        candidate_id: Optional[str] = None,
        job_id: Optional[str] = None,
        skill: Optional[str] = None,
        level: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Retrieves templates, formats parameters, invokes LLM, and returns structured questions guide.
        """
        # 1. Resolve Candidate Details
        candidate_details = "No candidate profile provided."
        candidate_name = "Candidate"
        if candidate_id:
            candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
            if candidate:
                candidate_name = f"{candidate.first_name} {candidate.last_name}"
                res = db.query(ParsedResumeData).join(Resume).filter(Resume.candidate_id == candidate_id).first()
                if res:
                    candidate_details = (
                        f"Name: {candidate_name}\n"
                        f"Experience: {candidate.total_experience_years} years\n"
                        f"Skills: {', '.join(candidate.skills or [])}\n"
                        f"Current Company: {res.current_company or 'N/A'}\n"
                        f"Education: {json.dumps(res.education or [])}\n"
                        f"Work History: {json.dumps(res.work_experience or [])}\n"
                        f"Projects: {json.dumps(res.projects or [])}"
                    )
                else:
                    candidate_details = (
                        f"Name: {candidate_name}\n"
                        f"Experience: {candidate.total_experience_years} years\n"
                        f"Skills: {', '.join(candidate.skills or [])}"
                    )

        # 2. Resolve Job Details
        job_details = "No job description provided."
        job_title = "Role"
        if job_id:
            job = db.query(Job).filter(Job.id == job_id).first()
            if job:
                job_title = job.title
                job_details = (
                    f"Title: {job.title}\n"
                    f"Department: {job.department}\n"
                    f"Location: {job.location}\n"
                    f"Experience Level Required: {job.experience_level}\n"
                    f"Required Skills: {', '.join(job.required_skills or [])}\n"
                    f"Description: {job.description}"
                )
                if not skill and job.required_skills:
                    skill = job.required_skills[0]
                if not level:
                    level = job.experience_level

        # 3. Apply Defaults for skill / level
        if not skill:
            skill = "General"
        if not level:
            level = "Mid"

        # 4. Fetch Template from Database
        template_text = self._find_template(db, template_type, skill, level)

        # 5. Format Prompt
        prompt = template_text.format(
            skill=skill,
            level=level,
            candidate_details=candidate_details,
            job_details=job_details,
            candidate_name=candidate_name,
            job_title=job_title
        )

        # 6. Execute LLM call
        try:
            if self.provider == "gemini":
                response_text = self._call_gemini(prompt)
            elif self.provider == "openai":
                response_text = self._call_openai(prompt)
            else:
                raise InterviewServiceError("Invalid provider.")
                
            return self._parse_guide_response(response_text, skill, level, template_type)
        except Exception as e:
            logger.error(f"Failed to generate interview guide: {str(e)}")
            raise InterviewServiceError(f"LLM generation failed: {str(e)}")

    def generate_job_description(
        self,
        db: Session,
        title: str,
        department: str,
        location: str,
        experience_level: str,
        employment_type: str,
        key_skills: List[str],
        additional_requirements: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generates a comprehensive job description using LLM.
        """
        # Fetch JD generator template
        template_text = self._find_template(db, TemplateType.JD_GENERATOR, "General", "Mid")
        
        prompt = template_text.format(
            title=title,
            department=department,
            location=location,
            experience_level=experience_level,
            employment_type=employment_type,
            key_skills=", ".join(key_skills),
            additional_requirements=additional_requirements or "None"
        )
        
        try:
            if self.provider == "gemini":
                response_text = self._call_gemini(prompt)
            elif self.provider == "openai":
                response_text = self._call_openai(prompt)
            else:
                raise InterviewServiceError("Invalid provider.")
                
            return self._parse_jd_response(response_text, title, department)
        except Exception as e:
            logger.error(f"Failed to generate JD: {str(e)}")
            raise InterviewServiceError(f"LLM generation failed: {str(e)}")

    def _find_template(self, db: Session, type: TemplateType, skill: str, level: str) -> str:
        """
        Looks up prompt template with fallback precedence.
        """
        # 1. Exact match
        tpl = db.query(PromptTemplate).filter(
            PromptTemplate.type == type,
            PromptTemplate.skill == skill,
            PromptTemplate.level == level
        ).first()
        if tpl:
            return tpl.template_text

        # 2. General skill fallback
        tpl = db.query(PromptTemplate).filter(
            PromptTemplate.type == type,
            PromptTemplate.skill == "General",
            PromptTemplate.level == level
        ).first()
        if tpl:
            return tpl.template_text

        # 3. Mid level fallback
        tpl = db.query(PromptTemplate).filter(
            PromptTemplate.type == type,
            PromptTemplate.skill == skill,
            PromptTemplate.level == "Mid"
        ).first()
        if tpl:
            return tpl.template_text

        # 4. General Mid fallback
        tpl = db.query(PromptTemplate).filter(
            PromptTemplate.type == type,
            PromptTemplate.skill == "General",
            PromptTemplate.level == "Mid"
        ).first()
        if tpl:
            return tpl.template_text

        # 5. Global fallback to static defaults
        if type == TemplateType.TECHNICAL:
            return FALLBACK_TECHNICAL_TEMPLATE
        elif type == TemplateType.HR:
            return FALLBACK_HR_TEMPLATE
        elif type == TemplateType.MANAGERIAL:
            return FALLBACK_MANAGERIAL_TEMPLATE
        elif type == TemplateType.JD_GENERATOR:
            return FALLBACK_JD_TEMPLATE
            
        raise InterviewServiceError(f"Could not resolve template for type={type}")

    def _call_gemini(self, prompt: str) -> str:
        import google.generativeai as genai
        model = genai.GenerativeModel(settings.GEMINI_MODEL)
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json"
            )
        )
        return response.text.strip()

    def _call_openai(self, prompt: str) -> str:
        response = self.openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.7
        )
        return response.choices[0].message.content.strip()

    def _clean_json(self, text: str) -> str:
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        return text.strip()

    def _parse_guide_response(self, text: str, skill: str, level: str, type: TemplateType) -> Dict[str, Any]:
        text = self._clean_json(text)
        parsed = json.loads(text)
        
        # Enforce key validations
        parsed["role"] = parsed.get("role") or skill
        parsed["experience_level"] = parsed.get("experience_level") or level
        parsed["template_type"] = parsed.get("template_type") or type.value
        
        questions = parsed.get("questions") or []
        validated_questions = []
        for q in questions:
            validated_questions.append({
                "question": q.get("question") or "Tell me about your experience.",
                "expected_answer_points": q.get("expected_answer_points") or [],
                "evaluation_criteria": q.get("evaluation_criteria") or "Check clarity and technical depth.",
                "difficulty": str(q.get("difficulty") or "MEDIUM").upper()
            })
        parsed["questions"] = validated_questions
        return parsed

    def _parse_jd_response(self, text: str, title: str, department: str) -> Dict[str, Any]:
        text = self._clean_json(text)
        parsed = json.loads(text)
        
        # Enforce key validations
        parsed["title"] = parsed.get("title") or title
        parsed["department"] = parsed.get("department") or department
        parsed["description"] = parsed.get("description") or "Role overview..."
        parsed["required_skills"] = parsed.get("required_skills") or []
        return parsed
