import json
import logging
from typing import Dict, Any
from app.config import settings

logger = logging.getLogger(__name__)

class MatchingLLMError(Exception):
    """Raised when the matching LLM request fails."""
    pass

MATCHING_PROMPT = """
You are a senior recruitment evaluator AI. Your task is to perform a rigorous comparison between a Job Description and a Candidate's Profile (extracted from their resume).

Evaluate the following inputs:
- JOB TITLE: {job_title}
- JOB DESCRIPTION: {job_description}
- REQUIRED SKILLS: {required_skills}
- EXPERIENCE LEVEL REQUIRED: {job_experience_level}

- CANDIDATE NAME: {candidate_name}
- CANDIDATE EXPERIENCE: {candidate_experience_years} years
- CANDIDATE SKILLS: {candidate_skills}
- CANDIDATE CURRENT LOCATION: {candidate_location}
- CANDIDATE NOTICE PERIOD: {candidate_notice_period}
- CANDIDATE WORK HISTORY: {candidate_work_history}
- CANDIDATE PROJECTS: {candidate_projects}

Follow these evaluation rules strictly:
1. Provide a realistic match percentage (0 to 100). Do not assign high scores (e.g., above 80) unless the candidate meets the core technical skills and experience levels.
2. Penalize heavily if mandatory required skills are missing from candidate's skills and experience.
3. Compare the candidate's total years of experience against the level required.
4. Assess location fit (e.g. Remote vs Hybrid vs local location match) and notice period suitability.
5. Identify candidate's strengths and core concerns.
6. Make a final recommendation: "SHORTLIST" (very strong fit), "MAYBE" (some alignment, worth interviewing), or "REJECT" (weak fit).
7. Return ONLY a valid JSON object matching the JSON schema below. Do NOT wrap in markdown code blocks like ```json ... ```. Do not include any introductory or trailing text.

JSON Schema:
{{
  "candidate_id": "{candidate_id}",
  "match_percentage": 0.0,
  "skill_match_analysis": "Detailed explanation of which core skills match and which do not.",
  "matched_skills": ["string"],
  "missing_skills": ["string"],
  "experience_analysis": "Assessment of experience duration and quality.",
  "experience_delta": "Compare candidate's experience to job needs (e.g., 'Meets experience requirement', 'Lacks 2 years of experience').",
  "location_fit": "Analysis of candidate location compared to job location.",
  "notice_period_fit": "Analysis of candidate notice period.",
  "strengths": ["string"],
  "concerns": ["string"],
  "final_recommendation": "SHORTLIST | MAYBE | REJECT",
  "summary": "Concise executive summary of why the candidate is or is not a fit."
}}
"""

class MatchingLLMService:
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
            raise MatchingLLMError(f"Unsupported LLM provider: {self.provider}")

    def evaluate_match(self, job_data: Dict[str, Any], candidate_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Runs the LLM evaluation comparing the job description against candidate details.
        Returns a structured dictionary matching the JSON output schema.
        """
        # Format the comparison prompt
        prompt = MATCHING_PROMPT.format(
            # Job details
            job_title=job_data.get("title", ""),
            job_description=job_data.get("description", ""),
            required_skills=job_data.get("required_skills", []),
            job_experience_level=job_data.get("experience_level", ""),
            
            # Candidate details
            candidate_id=candidate_data.get("id", ""),
            candidate_name=f"{candidate_data.get('first_name', '')} {candidate_data.get('last_name', '')}",
            candidate_experience_years=candidate_data.get("total_experience_years") or 0.0,
            candidate_skills=candidate_data.get("skills", []),
            candidate_location=candidate_data.get("current_location") or "Not specified",
            candidate_notice_period=candidate_data.get("notice_period") or "Not specified",
            candidate_work_history=json.dumps(candidate_data.get("work_experience") or []),
            candidate_projects=json.dumps(candidate_data.get("projects") or []),
        )

        max_retries = 3
        for attempt in range(max_retries):
            try:
                if self.provider == "gemini":
                    response_text = self._call_gemini(prompt)
                elif self.provider == "openai":
                    response_text = self._call_openai(prompt)
                else:
                    raise MatchingLLMError("Invalid provider configured.")
                    
                return self._clean_and_parse_json(response_text, candidate_data.get("id"))
                
            except Exception as e:
                logger.error(f"LLM matching failed (attempt {attempt + 1}/{max_retries}): {str(e)}")
                if attempt == max_retries - 1:
                    raise MatchingLLMError(f"LLM matching service failed: {str(e)}")
                import time
                time.sleep(2.0)

    def _call_gemini(self, prompt: str) -> str:
        import google.generativeai as genai
        model = genai.GenerativeModel(settings.GEMINI_MODEL)
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                temperature=0.1
            ),
            request_options={"timeout": 90.0}
        )
        return response.text.strip()

    def _call_openai(self, prompt: str) -> str:
        response = self.openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.1
        )
        return response.choices[0].message.content.strip()

    def _clean_and_parse_json(self, text: str, candidate_id: str) -> Dict[str, Any]:
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
            
        text = text.strip()
        parsed = json.loads(text)
        
        # Enforce schemas checks & defaults
        parsed["candidate_id"] = candidate_id
        
        # Ensure match_percentage is float
        try:
            parsed["match_percentage"] = float(parsed.get("match_percentage", 0.0))
        except (ValueError, TypeError):
            parsed["match_percentage"] = 0.0
            
        # Ensure lists are lists
        parsed["matched_skills"] = parsed.get("matched_skills") or []
        parsed["missing_skills"] = parsed.get("missing_skills") or []
        parsed["strengths"] = parsed.get("strengths") or []
        parsed["concerns"] = parsed.get("concerns") or []
        
        # Normalize final recommendation
        rec = str(parsed.get("final_recommendation", "REJECT")).upper()
        if rec not in ["SHORTLIST", "MAYBE", "REJECT"]:
            rec = "MAYBE"
        parsed["final_recommendation"] = rec

        return parsed
