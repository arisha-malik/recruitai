import logging
from typing import List
from app.config import settings

logger = logging.getLogger(__name__)

class EmbeddingConfigurationError(Exception):
    """Raised when the embedding service is improperly configured."""
    pass

class EmbeddingGenerationError(Exception):
    """Raised when embedding API call fails."""
    pass

class EmbeddingService:
    def __init__(self):
        self.provider = settings.EMBEDDING_PROVIDER.lower()
        self.model_name = settings.EMBEDDING_MODEL
        self._init_provider()

    def _init_provider(self):
        if self.provider == "gemini":
            if not settings.GEMINI_API_KEY:
                logger.warning("GEMINI_API_KEY is not set. Embedding service will fail unless mocked.")
            import google.generativeai as genai
            genai.configure(api_key=settings.GEMINI_API_KEY)
        elif self.provider == "openai":
            if not settings.OPENAI_API_KEY:
                logger.warning("OPENAI_API_KEY is not set. Embedding service will fail unless mocked.")
            from openai import OpenAI
            self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        else:
            raise EmbeddingConfigurationError(f"Unsupported embedding provider: {self.provider}")

    def get_embedding_dimension(self) -> int:
        """
        Returns the vector dimension size of the configured embedding model.
        """
        if self.provider == "gemini":
            # text-embedding-004 is 768 dimensions
            return 768
        elif self.provider == "openai":
            # text-embedding-3-small is 1536 dimensions
            return 1536
        return 768

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generates vector embedding for the input text using the configured provider.
        """
        if not text or not text.strip():
            raise EmbeddingGenerationError("Cannot generate embedding for empty text.")
            
        try:
            if self.provider == "gemini":
                return self._call_gemini(text)
            elif self.provider == "openai":
                return self._call_openai(text)
            else:
                raise EmbeddingGenerationError("Invalid provider configured.")
        except Exception as e:
            logger.error(f"Failed to generate embedding: {str(e)}")
            raise EmbeddingGenerationError(f"Embedding API call failed: {str(e)}")

    def _call_gemini(self, text: str) -> List[float]:
        import google.generativeai as genai
        
        # Ensure model is correctly prefixed
        model = self.model_name
        if not model.startswith("models/"):
            model = f"models/{model}"
            
        result = genai.embed_content(
            model=model,
            content=text,
            task_type="retrieval_document"
        )
        return result["embedding"]

    def _call_openai(self, text: str) -> List[float]:
        response = self.openai_client.embeddings.create(
            input=[text],
            model=self.model_name
        )
        return response.data[0].embedding

def build_candidate_profile_summary(parsed_data: dict) -> str:
    """
    Builds a coherent, semantically rich plain text summary of a candidate profile
    for generating vector embeddings.
    """
    name = parsed_data.get("full_name") or "Candidate"
    skills = parsed_data.get("technical_skills") or []
    experience = parsed_data.get("total_experience_years")
    current_company = parsed_data.get("current_company")
    current_location = parsed_data.get("current_location")
    
    summary_parts = []
    
    # 1. Headline
    headline = f"{name}"
    if current_location:
        headline += f" based in {current_location}"
    if experience is not None:
        headline += f" with {experience} years of total professional experience"
    headline += "."
    summary_parts.append(headline)

    # 2. Skills
    if skills:
        summary_parts.append(f"Skills and technical expertise include: {', '.join(skills)}.")

    # 3. Work Experience Summary
    work = parsed_data.get("work_experience") or []
    if work and isinstance(work, list):
        jobs_list = []
        for job in work[:3]: # top 3 jobs
            role = job.get("role") or "Software Engineer"
            company = job.get("company") or "Tech Company"
            desc = job.get("description") or ""
            job_summary = f"Worked as {role} at {company}"
            if desc:
                # Add key parts of description
                job_summary += f", focusing on {desc[:100]}"
            jobs_list.append(job_summary)
        summary_parts.append("Employment history: " + "; ".join(jobs_list) + ".")
    elif current_company:
        summary_parts.append(f"Currently working at {current_company}.")

    # 4. Education and Projects
    projects = parsed_data.get("projects") or []
    if projects and isinstance(projects, list):
        proj_list = []
        for proj in projects[:2]: # top 2 projects
            title = proj.get("title") or "Project"
            tech = proj.get("technologies") or []
            desc = proj.get("description") or ""
            proj_summary = f"Developed project '{title}'"
            if tech:
                proj_summary += f" using {', '.join(tech)}"
            if desc:
                proj_summary += f", details: {desc[:100]}"
            proj_list.append(proj_summary)
        summary_parts.append("Key projects: " + "; ".join(proj_list) + ".")

    return " ".join(summary_parts)

def build_job_profile_summary(job_data: dict) -> str:
    """
    Builds a clean, semantically rich plain text summary of a job description
    for generating vector embeddings.
    """
    title = job_data.get("title") or ""
    department = job_data.get("department") or ""
    location = job_data.get("location") or ""
    emp_type = job_data.get("employment_type") or ""
    exp_level = job_data.get("experience_level") or ""
    desc = job_data.get("description") or ""
    skills = job_data.get("required_skills") or []

    summary_parts = []
    
    # 1. Headline
    headline = f"{title} role in {department} department located in {location}."
    if exp_level:
        headline += f" Requires {exp_level} level of experience."
    if emp_type:
        headline += f" Employment type is {emp_type}."
    summary_parts.append(headline)

    # 2. Required skills
    if skills:
        summary_parts.append(f"Required skills and core technologies: {', '.join(skills)}.")

    # 3. Description
    if desc:
        summary_parts.append(f"Responsibilities and description: {desc}")

    return " ".join(summary_parts)
