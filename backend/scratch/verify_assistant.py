import os
import sys
import uuid
import json
from unittest.mock import patch, MagicMock

# Add backend directory to path
backend_path = r"c:\Users\HP\Documents\VS Code\AATA\backend"
sys.path.insert(0, backend_path)

# Set env variables before importing app
os.environ["DATABASE_URL"] = "sqlite:///verify_assistant.db"
os.environ["QDRANT_ENABLED"] = "false"
os.environ["RUN_JOBS_SYNC"] = "true"
os.environ["GEMINI_API_KEY"] = "mock_gemini_key"

from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine, SessionLocal
from app.models.user import User, UserRole
from app.models.candidate import Candidate
from app.models.job import Job
from app.models.assistant import GeneratedJobDescription, GeneratedInterviewQuestion
from app.models.audit import RecruitmentEvent

# Re-create database schema on our temporary SQLite file
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

client = TestClient(app)

MOCK_JD_DATA = {
    "job_title": "AI Engineer",
    "department": "Engineering",
    "location": "Remote",
    "employment_type": "FULL_TIME",
    "work_mode": "REMOTE",
    "experience_level": "Senior",
    "summary": "AI Engineering position.",
    "responsibilities": ["Develop machine learning models", "Deploy to AWS"],
    "required_skills": ["Python", "FastAPI"],
    "nice_to_have_skills": ["Docker", "Kubernetes"],
    "qualifications": ["CS Degree or equivalent experience"],
    "benefits": ["Medical", "Dental", "401k"],
    "full_job_description": "We are seeking a Senior AI Engineer..."
}

MOCK_QUESTIONS_DATA = {
    "type": "TECHNICAL",
    "focus_skills": ["Python", "FastAPI"],
    "level": "SENIOR",
    "questions": [
        {
            "question": "What is dependency injection in FastAPI?",
            "expected_answer_points": [
                "Uses Depends() function",
                "Swappable components",
                "Simplifies unit testing"
            ],
            "difficulty": "MEDIUM",
            "reason_for_asking": "Assess core FastAPI framework knowledge."
        }
    ]
}

@patch("app.services.assistant_service.AssistantService._call_gemini")
def run_tests(mock_gemini):
    print("--- STARTING JD & INTERVIEW ASSISTANT INTEGRATION TESTS ---")
    
    # Configure mock returns
    def mock_gemini_side_effect(prompt):
        if "Focus on practical skill depth" in prompt or "TECHNICAL" in prompt:
            return json.dumps(MOCK_QUESTIONS_DATA)
        return json.dumps(MOCK_JD_DATA)
        
    mock_gemini.side_effect = mock_gemini_side_effect
    
    db = SessionLocal()

    # Setup User roles
    print("\n1. Creating users for role checking...")
    r = client.post("/api/v1/auth/signup", json={
        "email": "recruiter@recruitai.com",
        "password": "recruiterpass",
        "first_name": "Sarah",
        "last_name": "Jenkins",
        "role": "RECRUITER"
    })
    assert r.status_code == 201
    
    r = client.post("/api/v1/auth/signup", json={
        "email": "interviewer@recruitai.com",
        "password": "interviewerpass",
        "first_name": "Bob",
        "last_name": "Smith",
        "role": "INTERVIEWER"
    })
    assert r.status_code == 201
    
    # Logins
    recruiter_token = client.post("/api/v1/auth/login", data={"username": "recruiter@recruitai.com", "password": "recruiterpass"}).json()["access_token"]
    recruiter_headers = {"Authorization": f"Bearer {recruiter_token}"}
    
    interviewer_token = client.post("/api/v1/auth/login", data={"username": "interviewer@recruitai.com", "password": "interviewerpass"}).json()["access_token"]
    interviewer_headers = {"Authorization": f"Bearer {interviewer_token}"}
    
    # Test 1: JD Generation works and saves to generated outputs table
    print("\n2. Testing JD generation (save_to_job=false)...")
    r = client.post("/api/v1/assistant/generate-jd?save_to_job=false", json={
        "role": "AI Engineer",
        "department": "Engineering",
        "experience_level": "Senior",
        "required_skills": ["Python", "FastAPI"],
        "nice_to_have_skills": ["Docker"],
        "location": "Remote",
        "employment_type": "FULL_TIME",
        "work_mode": "REMOTE",
        "responsibilities_hint": "Building NLP microservices"
    }, headers=recruiter_headers)
    
    assert r.status_code == 200
    jd_res = r.json()
    assert jd_res["status"] == "success"
    assert jd_res["job_id"] is None
    assert jd_res["data"]["job_title"] == "AI Engineer"
    
    # Check that a record was added to generated_job_descriptions
    gen_id = jd_res["generated_jd_id"]
    db_jd = db.query(GeneratedJobDescription).filter(GeneratedJobDescription.id == gen_id).first()
    assert db_jd is not None
    assert db_jd.generated_json["job_title"] == "AI Engineer"
    print("Success: Generated JD persisted to database.")
    
    # Check that JD_GENERATED event was logged
    event = db.query(RecruitmentEvent).filter(RecruitmentEvent.event_type == "JD_GENERATED").first()
    assert event is not None
    assert event.metadata_json["generated_jd_id"] == gen_id
    print("Success: JD_GENERATED event logged.")

    # Test 2: JD Generation optionally saves to jobs table
    print("\n3. Testing JD generation and save to jobs table (save_to_job=true)...")
    r = client.post("/api/v1/assistant/generate-jd?save_to_job=true", json={
        "role": "AI Engineer",
        "department": "Engineering",
        "experience_level": "Senior",
        "required_skills": ["Python", "FastAPI"],
        "nice_to_have_skills": ["Docker"],
        "location": "Remote",
        "employment_type": "FULL_TIME",
        "work_mode": "REMOTE",
        "responsibilities_hint": "Building NLP microservices"
    }, headers=recruiter_headers)
    
    assert r.status_code == 200
    jd_save_res = r.json()
    assert jd_save_res["job_id"] is not None
    
    # Verify job record is saved in jobs table
    saved_job_id = jd_save_res["job_id"]
    job_record = db.query(Job).filter(Job.id == saved_job_id).first()
    assert job_record is not None
    assert job_record.title == "AI Engineer"
    assert job_record.experience_level == "Senior"
    print(f"Success: Job saved to jobs database with ID: {saved_job_id}")

    # Test 3: Interview questions generate with only skills
    print("\n4. Testing Interview Questions generation (skills only)...")
    r = client.post("/api/v1/assistant/interview-questions", json={
        "skills": ["Python", "FastAPI"],
        "level": "SENIOR",
        "type": "TECHNICAL",
        "number_of_questions": 5
    }, headers=recruiter_headers)
    
    assert r.status_code == 200
    q_res = r.json()
    assert q_res["status"] == "success"
    assert q_res["data"]["type"] == "TECHNICAL"
    assert len(q_res["data"]["questions"]) == 1
    
    # Verify saved in generated_interview_questions table
    gen_q_id = q_res["generated_questions_id"]
    db_q = db.query(GeneratedInterviewQuestion).filter(GeneratedInterviewQuestion.id == gen_q_id).first()
    assert db_q is not None
    assert db_q.type == "TECHNICAL"
    assert db_q.level == "SENIOR"
    print("Success: Generated questions persisted to database.")
    
    # Verify INTERVIEW_QUESTIONS_GENERATED event was logged
    event_q = db.query(RecruitmentEvent).filter(RecruitmentEvent.event_type == "INTERVIEW_QUESTIONS_GENERATED").first()
    assert event_q is not None
    assert event_q.metadata_json["generated_questions_id"] == gen_q_id
    print("Success: INTERVIEW_QUESTIONS_GENERATED event logged.")

    # Test 4: Interview questions generate with candidate_id and job_id
    print("\n5. Testing Interview Questions generation with candidate & job IDs...")
    # Add dummy candidate
    cand_id = str(uuid.uuid4())
    cand = Candidate(
        id=cand_id,
        first_name="Rahul",
        last_name="Sharma",
        email="rahul.sharma@gmail.com",
        skills=["Python", "FastAPI"]
    )
    db.add(cand)
    db.commit()
    
    r = client.post("/api/v1/assistant/interview-questions", json={
        "candidate_id": cand_id,
        "job_id": saved_job_id,
        "skills": [],
        "level": "SENIOR",
        "type": "TECHNICAL",
        "number_of_questions": 5
    }, headers=recruiter_headers)
    assert r.status_code == 200
    print("Success: Customized questions generated successfully.")

    # Test 5: RBAC Role Protection prevents unauthorized access
    print("\n6. Testing RBAC role protection...")
    # Interviewer role should be blocked from JD generator
    r = client.post("/api/v1/assistant/generate-jd?save_to_job=false", json={
        "role": "AI Engineer",
        "department": "Engineering",
        "experience_level": "Senior",
        "required_skills": ["Python"],
        "nice_to_have_skills": [],
        "location": "Remote",
        "employment_type": "FULL_TIME",
        "work_mode": "REMOTE"
    }, headers=interviewer_headers)
    assert r.status_code == 403
    print("Success: Role guard correctly blocks Interviewer role from JD Generation.")
    
    # Interviewer role should be ALLOWED to generate interview questions
    r = client.post("/api/v1/assistant/interview-questions", json={
        "skills": ["Python"],
        "level": "SENIOR",
        "type": "TECHNICAL"
    }, headers=interviewer_headers)
    assert r.status_code == 200
    print("Success: Interviewer role successfully authorized for Questions Generation.")

    # Test 6: Failed Gemini response handle
    print("\n7. Testing failure execution handling...")
    mock_gemini.side_effect = Exception("Gemini API Rate Limit Exceeded!")
    r = client.post("/api/v1/assistant/generate-jd?save_to_job=false", json={
        "role": "AI Engineer",
        "department": "Engineering",
        "experience_level": "Senior",
        "required_skills": ["Python"],
        "nice_to_have_skills": [],
        "location": "Remote",
        "employment_type": "FULL_TIME",
        "work_mode": "REMOTE"
    }, headers=recruiter_headers)
    assert r.status_code == 500
    
    # Assert JD_GENERATION_FAILED event was logged
    fail_event = db.query(RecruitmentEvent).filter(RecruitmentEvent.event_type == "JD_GENERATION_FAILED").first()
    assert fail_event is not None
    assert "Rate Limit" in fail_event.metadata_json["error"]
    print("Success: Failure handled gracefully and event logged.")

    db.close()
    engine.dispose()
    
    # Clean up test SQLite database
    try:
        os.remove("verify_assistant.db")
        print("\n8. Test database cleaned up.")
    except Exception as e:
        print(f"Cleanup warning: {str(e)}")

    print("\n--- ALL JD & INTERVIEW ASSISTANT INTEGRATION TESTS PASSED SUCCESSFULLY! ---")

if __name__ == "__main__":
    run_tests()
