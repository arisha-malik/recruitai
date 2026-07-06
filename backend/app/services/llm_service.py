import json
import logging
from typing import Dict, Any, List
from app.config import settings

logger = logging.getLogger(__name__)

class LLMConfigurationError(Exception):
    """Raised when the LLM service is improperly configured."""
    pass

class LLMParsingError(Exception):
    """Raised when the LLM response cannot be parsed or is invalid."""
    pass

# System instructions and schema definition
SEARCH_QUERY_PARSING_PROMPT = """
You are an expert recruitment AI assistant. The user has entered a natural language search query to find candidates in a database.
Your task is to parse this natural language query into structured JSON filters.

Extract any mentioned:
1. "skills" (list of strings): technical skills like Java, Python, AWS, Kubernetes, etc.
2. "roles" (list of strings): job titles like Developer, DevOps Engineer, Manager, etc.
3. "locations" (list of strings): locations like New York, London, Remote, etc.
4. "min_experience_years" (float or null): minimum years of experience if mentioned.
5. "notice_period" (string or null): notice period if mentioned (e.g. "Immediate", "30 days").
6. "education" (string or null): education requirements if mentioned (e.g. "Bachelor", "Computer Science").
7. "certifications" (list of strings): certifications if mentioned (e.g. "AWS Certified").

JSON Schema:
{{
  "skills": ["string"],
  "roles": ["string"],
  "locations": ["string"],
  "min_experience_years": "number | null",
  "notice_period": "string | null",
  "education": "string | null",
  "certifications": ["string"]
}}

Search Query:
---
{query}
---
"""

RESUME_PARSING_PROMPT = """
You are an expert recruitment AI assistant. Your task is to analyze the extracted plain text from a resume and convert it into a strict JSON object.

Follow these rules closely:
1. Extract the information matching the JSON schema below.
2. Return ONLY the raw JSON object. Do NOT wrap it in markdown code blocks like ```json ... ```. Do NOT include any introductory or concluding text.
3. Do NOT guess or hallucinate any details. If a specific field is not mentioned or cannot be inferred with high confidence, set its value to null (or an empty list if it's an array field).
4. Extract total experience in years as a float/integer number.
5. Deduplicate lists like technical_skills and certifications.

JSON Schema:
{{
  "full_name": "string | null",
  "email": "string | null",
  "mobile_number": "string | null",
  "total_experience_years": "number (integer or float) | null",
  "technical_skills": ["string"],
  "education": [
    {{
      "institution": "string | null",
      "degree": "string | null",
      "field_of_study": "string | null",
      "start_year": "string | null",
      "end_year": "string | null",
      "cgpa": "string | null (Include CGPA, marks, or percentage if explicitly stated in the resume)",
      "location": "string | null"
    }}
  ],
  "certifications": ["string"],
  "current_company": "string | null",
  "current_location": "string | null",
  "notice_period": "string | null",
  "work_experience": [
    {{
      "company": "string | null",
      "role": "string | null",
      "start_date": "string | null",
      "end_date": "string | null",
      "description": "string | null",
      "technologies_used": ["string"],
      "key_achievements": ["string"]
    }}
  ],
  "projects": [
    {{
      "title": "string | null",
      "description": "string | null",
      "technologies": ["string"],
      "links": ["string"],
      "key_features": ["string"]
    }}
  ]
}}

Extracted resume text:
---
{resume_text}
---
"""

class LLMService:
    def __init__(self):
        self.provider = settings.LLM_PROVIDER.lower()
        self._init_provider()

    def _init_provider(self):
        if self.provider == "gemini":
            if not settings.GEMINI_API_KEY:
                logger.warning("GEMINI_API_KEY is not set. LLM service calls will fail unless mocked.")
            import google.generativeai as genai
            genai.configure(api_key=settings.GEMINI_API_KEY)
        elif self.provider == "openai":
            if not settings.OPENAI_API_KEY:
                logger.warning("OPENAI_API_KEY is not set. LLM service calls will fail unless mocked.")
            from openai import OpenAI
            self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        else:
            raise LLMConfigurationError(f"Unsupported LLM provider: {self.provider}")

    def parse_resume_text(self, text: str) -> Dict[str, Any]:
        """
        Sends resume text to the selected LLM provider and parses the structured JSON output.
        """
        formatted_prompt = RESUME_PARSING_PROMPT.format(resume_text=text)
        
        try:
            if self.provider == "gemini":
                parsed_json = self._call_gemini(formatted_prompt)
            elif self.provider == "openai":
                parsed_json = self._call_openai(formatted_prompt)
            else:
                raise LLMParsingError("Invalid LLM provider configured.")
                
            # Perform post-processing and normalizations
            return self._normalize_parsed_data(parsed_json)
            
        except Exception as e:
            logger.error(f"LLM parsing failed: {str(e)}. Falling back to regex heuristic.")
            
            # Basic regex fallback to extract data from text if LLM fails (e.g. missing API key)
            import re
            
            email = None
            email_match = re.search(r'[\w\.-]+@[\w\.-]+', text)
            if email_match:
                email = email_match.group(0)
                
            mobile = None
            phone_match = re.search(r'\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}', text)
            if phone_match:
                mobile = phone_match.group(0)
                
            lines = [l.strip() for l in text.split('\n') if l.strip()]
            # Naive guess: first non-empty line is the name
            name = lines[0] if lines else "Candidate Name"
            if len(name) > 50:
                name = name[:50]
                
            skills = []
            for s in ["Python", "React", "TypeScript", "SQL", "JavaScript", "AWS", "Node.js"]:
                if s.lower() in text.lower():
                    skills.append(s)
            
            mock_json = {
                "full_name": name,
                "email": email,
                "mobile_number": mobile,
                "total_experience_years": None,
                "technical_skills": skills,
                "education": [],
                "certifications": [],
                "current_company": None,
                "current_location": None,
                "notice_period": None,
                "work_experience": [],
                "projects": []
            }
            return self._normalize_parsed_data(mock_json)

    def _call_gemini(self, prompt: str) -> Dict[str, Any]:
        import google.generativeai as genai
        
        # Use configurable Gemini model
        model = genai.GenerativeModel(settings.GEMINI_MODEL)
        
        # Request JSON output specifically
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json"
            )
        )
        
        response_text = response.text.strip()
        return self._clean_and_parse_json(response_text)

    def _call_openai(self, prompt: str) -> Dict[str, Any]:
        response = self.openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.1
        )
        response_text = response.choices[0].message.content.strip()
        return self._clean_and_parse_json(response_text)

    def _clean_and_parse_json(self, text: str) -> Dict[str, Any]:
        """Cleans potential markdown markers and loads the JSON object."""
        # Strip markdown ```json and ``` if present
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
            
        text = text.strip()
        return json.loads(text)

    def _normalize_parsed_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalizes obvious skill names and ensures all expected fields exist with appropriate fallbacks.
        """
        # Define normalizations map
        normalization_map = {
            "js": "JavaScript",
            "javascript": "JavaScript",
            "postgres": "PostgreSQL",
            "postgresql": "PostgreSQL",
            "node": "Node.js",
            "nodejs": "Node.js",
            "reactjs": "React",
            "react": "React",
            "aws": "AWS",
            "docker": "Docker",
            "kubernetes": "Kubernetes",
            "py": "Python",
            "python": "Python"
        }

        # 1. Clean technical skills
        skills = data.get("technical_skills", [])
        if not isinstance(skills, list):
            skills = []
            
        cleaned_skills = []
        for skill in skills:
            if not skill:
                continue
            skill_stripped = str(skill).strip()
            skill_lower = skill_stripped.lower()
            
            # Map normalized skill if matches, otherwise use standard capitalized representation
            normalized = normalization_map.get(skill_lower, skill_stripped)
            cleaned_skills.append(normalized)
            
        # Deduplicate and sort
        data["technical_skills"] = sorted(list(set(cleaned_skills)))

        # 2. Clean certifications
        certs = data.get("certifications", [])
        if not isinstance(certs, list):
            certs = []
        data["certifications"] = sorted(list(set([str(c).strip() for c in certs if c])))

        # 3. Ensure other fields default properly
        data["full_name"] = data.get("full_name") or None
        data["email"] = data.get("email") or None
        data["mobile_number"] = data.get("mobile_number") or None
        
        # Ensure experience is numeric or None
        exp = data.get("total_experience_years")
        if exp is not None:
            try:
                data["total_experience_years"] = float(exp)
            except (ValueError, TypeError):
                data["total_experience_years"] = None
        else:
            data["total_experience_years"] = None

        return data

    def parse_search_query(self, query: str) -> Dict[str, Any]:
        """
        Parses a natural language search query into structured filters.
        """
        formatted_prompt = SEARCH_QUERY_PARSING_PROMPT.format(query=query)
        
        try:
            if self.provider == "gemini":
                parsed_json = self._call_gemini(formatted_prompt)
            elif self.provider == "openai":
                parsed_json = self._call_openai(formatted_prompt)
            else:
                raise LLMParsingError("Invalid LLM provider configured.")
                
            return parsed_json
        except Exception as e:
            logger.error(f"Search query parsing failed: {str(e)}")
            # Fallback to simple skill extraction
            return {
                "skills": [query.strip()] if query.strip() else [],
                "roles": [],
                "locations": [],
                "min_experience_years": None,
                "notice_period": None,
                "education": None,
                "certifications": []
            }

