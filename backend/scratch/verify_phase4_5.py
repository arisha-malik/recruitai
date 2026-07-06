import os
import sys
import uuid
import time
from unittest.mock import patch, MagicMock

# Add backend directory to path
backend_path = r"c:\Users\HP\Documents\VS Code\AATA\backend"
sys.path.insert(0, backend_path)

# Set database URL to local test sqlite database
os.environ["DATABASE_URL"] = "sqlite:///verify_phase4_5.db"

# Import FastAPI client and database models
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine, SessionLocal
from app.models.user import User, UserRole
from app.models.candidate import Candidate, Resume, ParsingStatus
from app.models.job import Job, MatchingStatus
from app.models.application import Application, ApplicationStatus, MatchResult, PromptTemplate, TemplateType
from app.models.audit import RecruitmentEvent

# Re-create database schema on our temporary SQLite file
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

client = TestClient(app)

# Mock responses for LLM
MOCK_INTERVIEW_GUIDE = {
    "role": "Python Developer",
    "experience_level": "Senior",
    "template_type": "TECHNICAL",
    "questions": [
        {
            "question": "What is the GIL in Python and how does it affect multi-threading?",
            "expected_answer_points": [
                "Global Interpreter Lock",
                "Prevents multiple threads from executing Python bytecodes at once",
                "Affects CPU-bound tasks but not I/O-bound tasks"
            ],
            "evaluation_criteria": "Deep understanding of Python thread concurrency and memory management.",
            "difficulty": "MEDIUM"
        }
    ]
}

MOCK_JD_OUTPUT = {
    "title": "Senior Python Backend Engineer",
    "department": "Engineering",
    "description": "# Senior Python Backend Engineer\n\nWe are looking for a Senior Python Developer with FastAPI expertise.",
    "required_skills": ["Python", "FastAPI", "PostgreSQL"]
}

@patch("app.services.interview_service.InterviewService._call_gemini")
@patch("app.services.interview_service.InterviewService._call_openai")
def run_tests(mock_openai, mock_gemini):
    print("--- STARTING PHASE 4 & 5 INTEGRATION TESTS ---")
    
    # Configure mock returns (return serialized JSON)
    import json
    mock_gemini.return_value = json.dumps(MOCK_INTERVIEW_GUIDE)
    
    # Switch behaviour when mock_gemini is called for JD Generator
    def mock_gemini_side_effect(prompt):
        if "metadata:" in prompt or "Title:" in prompt:
            return json.dumps(MOCK_JD_OUTPUT)
        return json.dumps(MOCK_INTERVIEW_GUIDE)
    mock_gemini.side_effect = mock_gemini_side_effect
    
    db = SessionLocal()

    # 1. Sign up admin user to query endpoints
    print("\n1. Creating Admin user...")
    r = client.post("/api/v1/auth/signup", json={
        "email": "admin@recruitai.com",
        "password": "adminpassword",
        "first_name": "Admin",
        "last_name": "User",
        "role": "ADMIN"
    })
    assert r.status_code == 201
    
    # Login to obtain JWT
    r = client.post("/api/v1/auth/login", data={"username": "admin@recruitai.com", "password": "adminpassword"})
    assert r.status_code == 200
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("Admin logged in successfully.")

    # 2. Test Seeding default prompt templates
    print("\n2. Testing default templates seeding...")
    r = client.post("/api/v1/templates/seed", headers=headers)
    assert r.status_code == 200
    res = r.json()
    assert res["success"] is True
    assert res["seeded_count"] == 4
    print(f"Success: {res['message']}")
    
    # Retrieve templates list
    r = client.get("/api/v1/templates/", headers=headers)
    assert r.status_code == 200
    templates = r.json()
    assert len(templates) == 4
    print(f"Seeded templates verified: {[t['type'] for t in templates]}")

    # 3. Test Prompt Template CRUD
    print("\n3. Testing Prompt Template CRUD endpoints...")
    # Create template
    r = client.post("/api/v1/templates/", json={
        "skill": "React",
        "level": "Senior",
        "type": "TECHNICAL",
        "template_text": "Custom React Template for {candidate_details}"
    }, headers=headers)
    assert r.status_code == 201
    new_tpl = r.json()
    tpl_id = new_tpl["id"]
    assert new_tpl["skill"] == "React"
    
    # Update template
    r = client.put(f"/api/v1/templates/{tpl_id}", json={
        "level": "Lead",
        "template_text": "Updated custom React Template for {candidate_details}"
    }, headers=headers)
    assert r.status_code == 200
    updated_tpl = r.json()
    assert updated_tpl["level"] == "Lead"
    
    # Delete template
    r = client.delete(f"/api/v1/templates/{tpl_id}", headers=headers)
    assert r.status_code == 204
    
    # Verify deletion
    r = client.get(f"/api/v1/templates/{tpl_id}", headers=headers)
    assert r.status_code == 404
    print("CRUD endpoints work as expected.")

    # 4. Test Interview Guide Generation
    print("\n4. Testing Interview Guide Generation...")
    r = client.post("/api/v1/interview/questions", json={
        "template_type": "TECHNICAL",
        "skill": "Python",
        "level": "Senior"
    }, headers=headers)
    assert r.status_code == 200
    guide = r.json()
    assert guide["role"] == "Python Developer"
    assert len(guide["questions"]) == 1
    assert guide["questions"][0]["difficulty"] == "MEDIUM"
    print(f"Guide generated successfully: {guide['questions'][0]['question']}")

    # 5. Test JD Generation
    print("\n5. Testing JD Generation...")
    r = client.post("/api/v1/interview/generate-jd", json={
        "title": "Senior Python Backend Engineer",
        "department": "Engineering",
        "location": "Remote, US",
        "experience_level": "Senior",
        "employment_type": "FULL_TIME",
        "key_skills": ["Python", "FastAPI"]
    }, headers=headers)
    assert r.status_code == 200
    jd = r.json()
    assert jd["title"] == "Senior Python Backend Engineer"
    assert "FastAPI" in jd["required_skills"]
    print("JD generated successfully.")

    # 6. Test Event Interceptors (Transparent logging on DB mutations)
    print("\n6. Testing SQLAlchemy event interceptors...")
    # Insert candidate & resume via upload API
    print("Presigning upload...")
    r = client.post("/api/v1/uploads/presigned-url", json={
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@gmail.com",
        "file_name": "john_resume.pdf",
        "file_type": "application/pdf"
    }, headers=headers)
    assert r.status_code == 200
    upload_res = r.json()
    cand_id = upload_res["candidate_id"]
    resume_id = upload_res["resume_id"]
    
    # Check that events CANDIDATE_CREATED and RESUME_UPLOADED were logged automatically
    cand_events = db.query(RecruitmentEvent).filter(RecruitmentEvent.candidate_id == cand_id).all()
    event_types = [e.event_type for e in cand_events]
    print(f"Events recorded for candidate: {event_types}")
    assert "CANDIDATE_CREATED" in event_types
    assert "RESUME_UPLOADED" in event_types
    
    # Create a Job
    r = client.post("/api/v1/jobs/", json={
        "title": "Python Developer",
        "department": "Engineering",
        "location": "Remote",
        "employment_type": "FULL_TIME",
        "experience_level": "Mid",
        "description": "Python Job description",
        "required_skills": ["Python"],
        "status": "OPEN"
    }, headers=headers)
    assert r.status_code == 201
    job_id = r.json()["id"]

    # Submit Application (Creates application)
    r = client.post("/api/v1/applications/", json={
        "candidate_id": cand_id,
        "job_id": job_id
    }, headers=headers)
    assert r.status_code == 201
    app_id = r.json()["id"]
    
    # Check APPLICATION_CREATED is logged
    app_events = db.query(RecruitmentEvent).filter(RecruitmentEvent.application_id == app_id).all()
    app_event_types = [e.event_type for e in app_events]
    print(f"Events recorded for application: {app_event_types}")
    assert "APPLICATION_CREATED" in app_event_types
    
    # Update application status to SHORTLISTED
    r = client.patch(f"/api/v1/applications/{app_id}/status", json={"status": "SHORTLISTED"}, headers=headers)
    assert r.status_code == 200
    
    # Check APPLICATION_STATUS_UPDATED is logged
    app_events_updated = db.query(RecruitmentEvent).filter(
        RecruitmentEvent.application_id == app_id,
        RecruitmentEvent.event_type == "APPLICATION_STATUS_UPDATED"
    ).all()
    assert len(app_events_updated) == 1
    meta = app_events_updated[0].metadata_json
    assert meta["old_status"] == "APPLIED"
    assert meta["new_status"] == "SHORTLISTED"
    print("SQLAlchemy event listeners successfully verified.")

    # 7. Test Dashboard Analytics
    print("\n7. Testing Dashboard Analytics aggregation...")
    # Add a MatchResult to DB so we have score metrics to test
    mr = MatchResult(
        id=str(uuid.uuid4()),
        candidate_id=cand_id,
        job_id=job_id,
        application_id=app_id,
        match_percentage=85.0,
        skill_match_analysis="Matches FastAPI",
        experience_delta="Meets requirement",
        location_fit="Fits",
        notice_period_fit="Fits",
        final_recommendation="SHORTLIST",
        summary="Good"
    )
    db.add(mr)
    db.commit()
    
    # A. Get summary
    r = client.get("/api/v1/analytics/dashboard/summary", headers=headers)
    assert r.status_code == 200
    summary = r.json()
    assert summary["total_candidates"] == 1
    assert summary["total_jobs"] == 1
    assert summary["total_applications"] == 1
    assert summary["total_matches"] == 1
    assert summary["shortlist_rate"] == 100.0
    print(f"Summary stats verified: {summary}")

    # B. Get funnel
    r = client.get(f"/api/v1/analytics/dashboard/funnel?job_id={job_id}", headers=headers)
    assert r.status_code == 200
    funnel = r.json()
    stages = {s["stage"]: s for s in funnel["stages"]}
    assert stages["APPLIED"]["count"] == 1
    assert stages["SHORTLISTED"]["count"] == 1
    print(f"Funnel stages counts verified: {[(s['stage'], s['count']) for s in funnel['stages']]}")

    # C. Get time-to-hire (Update application status to OFFERED to trigger logic)
    # Simulate time diff by updating applied_at to 5 days ago
    app_record = db.query(Application).filter(Application.id == app_id).first()
    app_record.applied_at = app_record.applied_at.replace(day=app_record.applied_at.day - 5) if app_record.applied_at.day > 5 else app_record.applied_at
    db.commit()
    
    r = client.patch(f"/api/v1/applications/{app_id}/status", json={"status": "OFFERED"}, headers=headers)
    assert r.status_code == 200
    
    r = client.get("/api/v1/analytics/dashboard/time-to-hire", headers=headers)
    assert r.status_code == 200
    tth = r.json()
    assert tth["overall"]["completed_hires_count"] == 1
    print(f"Time-to-hire verified: {tth['overall']}")

    # D. Get shortlisting statistics
    r = client.get(f"/api/v1/analytics/dashboard/shortlisting?job_id={job_id}", headers=headers)
    assert r.status_code == 200
    sl = r.json()
    assert sl["total_evaluated"] == 1
    assert sl["average_match_score"] == 85.0
    print(f"Shortlisting stats verified: Average={sl['average_match_score']}, Evaluated={sl['total_evaluated']}")

    db.close()
    engine.dispose()
    
    # Clean up test SQLite database
    try:
        os.remove("verify_phase4_5.db")
        print("\n8. Test files cleaned up.")
    except Exception as e:
        print(f"Cleanup warning: {str(e)}")

    print("\n--- ALL PHASE 4 & 5 INTEGRATION TESTS PASSED SUCCESSFULLY! ---")

if __name__ == "__main__":
    run_tests()
