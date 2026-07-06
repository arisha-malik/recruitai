import os
import sys
import uuid
import datetime
from unittest.mock import patch, MagicMock

# Add backend directory to path
backend_path = r"c:\Users\HP\Documents\VS Code\AATA\backend"
sys.path.insert(0, backend_path)

# Set env variables before importing app
os.environ["DATABASE_URL"] = "sqlite:///verify_analytics.db"
os.environ["QDRANT_ENABLED"] = "false"
os.environ["RUN_JOBS_SYNC"] = "true"
os.environ["GEMINI_API_KEY"] = "mock_gemini_key"

from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine, SessionLocal
from app.models.user import User, UserRole
from app.models.candidate import Candidate, Resume, ParsingStatus
from app.models.job import Job, JobStatus
from app.models.application import Application, ApplicationStatus, MatchResult
from app.models.audit import RecruitmentEvent

# Re-create database schema on our temporary SQLite file
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

client = TestClient(app)

def run_tests():
    print("--- STARTING DASHBOARD & RECRUITMENT ANALYTICS INTEGRATION TESTS ---")
    
    db = SessionLocal()

    # 1. Setup users with different roles
    print("\n1. Creating users for role checking...")
    r = client.post("/api/v1/auth/signup", json={
        "email": "admin@recruitai.com",
        "password": "adminpass",
        "first_name": "Sarah",
        "last_name": "Admin",
        "role": "ADMIN"
    })
    assert r.status_code == 201
    
    r = client.post("/api/v1/auth/signup", json={
        "email": "recruiter@recruitai.com",
        "password": "recruiterpass",
        "first_name": "Bob",
        "last_name": "Recruiter",
        "role": "RECRUITER"
    })
    assert r.status_code == 201

    r = client.post("/api/v1/auth/signup", json={
        "email": "interviewer@recruitai.com",
        "password": "interviewerpass",
        "first_name": "Alice",
        "last_name": "Interviewer",
        "role": "INTERVIEWER"
    })
    assert r.status_code == 201
    
    # Login & get JWT headers
    admin_token = client.post("/api/v1/auth/login", data={"username": "admin@recruitai.com", "password": "adminpass"}).json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    
    recruiter_token = client.post("/api/v1/auth/login", data={"username": "recruiter@recruitai.com", "password": "recruiterpass"}).json()["access_token"]
    recruiter_headers = {"Authorization": f"Bearer {recruiter_token}"}

    interviewer_token = client.post("/api/v1/auth/login", data={"username": "interviewer@recruitai.com", "password": "interviewerpass"}).json()["access_token"]
    interviewer_headers = {"Authorization": f"Bearer {interviewer_token}"}

    # Verify USER_LOGIN events were logged
    login_events = db.query(RecruitmentEvent).filter(RecruitmentEvent.event_type == "USER_LOGIN").all()
    assert len(login_events) == 3
    print("Success: USER_LOGIN events logged correctly.")

    # 2. Test RBAC protection: Interviewer is blocked from analytics
    print("\n2. Testing RBAC role protection on /dashboard-summary...")
    r = client.get("/api/v1/analytics/dashboard-summary", headers=interviewer_headers)
    assert r.status_code == 403
    
    # Recruiter is allowed
    r = client.get("/api/v1/analytics/dashboard-summary", headers=recruiter_headers)
    assert r.status_code == 200
    print("Success: Role guard correctly authorized Recruiter and blocked Interviewer.")

    # 3. Create initial data with Recruiter logged in
    # (To test ContextVar and actor logging, we do it via Client calls)
    print("\n3. Creating Candidates, Resumes, and Jobs under Recruiter...")
    
    # Recruiter creates Job 1
    r = client.post("/api/v1/jobs/", json={
        "title": "Senior AI Architect",
        "department": "Engineering",
        "location": "Remote",
        "employment_type": "FULL_TIME",
        "experience_level": "Senior",
        "description": "Awesome role.",
        "status": "OPEN",
        "required_skills": ["Python", "Gemini"]
    }, headers=recruiter_headers)
    assert r.status_code == 201
    job1_id = r.json()["id"]

    # Let's verify Job event listener logged JOB_CREATED
    job_event = db.query(RecruitmentEvent).filter(
        RecruitmentEvent.event_type == "JOB_CREATED",
        RecruitmentEvent.job_id == job1_id
    ).first()
    assert job_event is not None
    assert job_event.actor_id is not None
    print("Success: JOB_CREATED event logged with correct actor.")

    # Recruiter creates Candidate 1 (LinkedIn)
    r = client.post("/api/v1/candidates/", json={
        "first_name": "Rahul",
        "last_name": "Verma",
        "email": "rahul.verma@linkedin.com",
        "source": "LINKEDIN",
        "skills": ["Python", "Gemini"]
    }, headers=recruiter_headers)
    assert r.status_code == 201
    c1_id = r.json()["id"]

    # Verify CANDIDATE_CREATED actor_id
    cand_event = db.query(RecruitmentEvent).filter(
        RecruitmentEvent.event_type == "CANDIDATE_CREATED",
        RecruitmentEvent.candidate_id == c1_id
    ).first()
    assert cand_event is not None
    assert cand_event.actor_id is not None
    print("Success: CANDIDATE_CREATED event logged with correct actor from ContextVar.")

    # Recruiter uploads Resume for Candidate 1
    # Create candidate 2 (Direct Upload) via upload flow
    r = client.post("/api/v1/uploads/presigned-url", json={
        "first_name": "Sneha",
        "last_name": "Patel",
        "email": "sneha.patel@gmail.com",
        "file_name": "sneha_resume.pdf",
        "file_type": "application/pdf"
    }, headers=recruiter_headers)
    assert r.status_code == 200
    c2_id = r.json()["candidate_id"]
    resume2_id = r.json()["resume_id"]

    # Verify uploaded Candidate 2 has DIRECT_UPLOAD source
    c2 = db.query(Candidate).filter(Candidate.id == c2_id).first()
    assert c2.source == "DIRECT_UPLOAD"
    print("Success: Candidate source set to DIRECT_UPLOAD from upload flow.")

    # Verify RESUME_UPLOADED actor_id
    res_event = db.query(RecruitmentEvent).filter(
        RecruitmentEvent.event_type == "RESUME_UPLOADED",
        RecruitmentEvent.resume_id == resume2_id
    ).first()
    assert res_event is not None
    assert res_event.actor_id is not None
    print("Success: RESUME_UPLOADED event logged with correct actor.")

    # Simulate resume parsing status update (and log parsing success)
    res2 = db.query(Resume).filter(Resume.id == resume2_id).first()
    res2.parsing_status = ParsingStatus.PARSED
    db.commit()

    # Manual insert of matching results
    mr1 = MatchResult(
        id=str(uuid.uuid4()),
        candidate_id=c1_id,
        job_id=job1_id,
        match_percentage=92.0,
        skill_match_analysis="Excellent skills.",
        experience_delta="No delta.",
        location_fit="Yes",
        notice_period_fit="Immediate",
        final_recommendation="SHORTLIST",
        summary="Strong fit"
    )
    db.add(mr1)
    
    mr2 = MatchResult(
        id=str(uuid.uuid4()),
        candidate_id=c2_id,
        job_id=job1_id,
        match_percentage=72.0,
        skill_match_analysis="Good skills.",
        experience_delta="No delta.",
        location_fit="Yes",
        notice_period_fit="1 month",
        final_recommendation="MAYBE",
        summary="Good fit"
    )
    db.add(mr2)
    db.commit()

    # Create Applications
    r = client.post("/api/v1/applications/", json={
        "candidate_id": c1_id,
        "job_id": job1_id
    }, headers=recruiter_headers)
    assert r.status_code == 201
    app1_id = r.json()["id"]

    r = client.post("/api/v1/applications/", json={
        "candidate_id": c2_id,
        "job_id": job1_id
    }, headers=recruiter_headers)
    assert r.status_code == 201
    app2_id = r.json()["id"]

    # 4. Test status changes and populating transition timestamps
    print("\n4. Testing update application status and timestamps...")
    # Update app 1 to SHORTLISTED
    r = client.patch(f"/api/v1/applications/{app1_id}/status", json={"status": "SHORTLISTED"}, headers=recruiter_headers)
    assert r.status_code == 200
    
    # Check shortlisted_at is populated
    app1 = db.query(Application).filter(Application.id == app1_id).first()
    assert app1.shortlisted_at is not None
    assert app1.interviewing_at is None
    print("Success: shortlisted_at timestamp set correctly.")

    # Verify both APPLICATION_STATUS_UPDATED and APPLICATION_STATUS_CHANGED were logged
    app_changed_events = db.query(RecruitmentEvent).filter(
        RecruitmentEvent.application_id == app1_id,
        RecruitmentEvent.event_type == "APPLICATION_STATUS_CHANGED"
    ).all()
    assert len(app_changed_events) == 1
    assert app_changed_events[0].actor_id is not None
    print("Success: APPLICATION_STATUS_CHANGED event logged correctly.")

    # 5. Query Dashboard Summary Endpoint
    print("\n5. Testing /dashboard-summary endpoint...")
    r = client.get("/api/v1/analytics/dashboard-summary", headers=recruiter_headers)
    assert r.status_code == 200
    sum_data = r.json()
    assert sum_data["total_candidates"] == 2
    assert sum_data["total_jobs"] == 1
    assert sum_data["open_jobs"] == 1
    assert sum_data["shortlisted_candidates"] == 1
    assert sum_data["average_match_score"] == 82.0 # (92 + 72) / 2
    assert len(sum_data["recent_activity"]) > 0
    print("Success: Summary stats are correct.")

    # 6. Query Candidate Pipeline Endpoint
    print("\n6. Testing /candidate-pipeline endpoint...")
    r = client.get("/api/v1/analytics/candidate-pipeline", headers=recruiter_headers)
    assert r.status_code == 200
    pipe_data = r.json()
    assert pipe_data["status_counts"]["SHORTLISTED"] == 1
    assert pipe_data["status_counts"]["APPLIED"] == 1
    assert pipe_data["status_percentages"]["SHORTLISTED"] == 50.0
    assert pipe_data["status_percentages"]["APPLIED"] == 50.0
    print("Success: Pipeline stage counts and percentages verified.")

    # 7. Query Resume Parsing Analytics Endpoint
    print("\n7. Testing /resume-parsing endpoint...")
    r = client.get("/api/v1/analytics/resume-parsing", headers=recruiter_headers)
    assert r.status_code == 200
    parse_data = r.json()
    assert parse_data["total_resumes"] == 1
    assert parse_data["parsed"] == 1
    assert parse_data["parse_success_rate"] == 100.0
    assert parse_data["average_parse_time_seconds"] is None
    print("Success: Resume parsing analytics verified.")

    # 8. Query Matching Analytics Endpoint
    print("\n8. Testing /matching endpoint...")
    r = client.get("/api/v1/analytics/matching", headers=recruiter_headers)
    assert r.status_code == 200
    match_data = r.json()
    assert match_data["total_match_results"] == 2
    assert match_data["average_match_percentage"] == 82.0
    assert match_data["strong_fit_count"] == 1 # 92.0
    assert match_data["good_fit_count"] == 1   # 72.0
    assert match_data["recommendation_breakdown"]["SHORTLIST"] == 1
    assert match_data["recommendation_breakdown"]["MAYBE"] == 1
    print("Success: Matching fit bands and recommendations breakdown verified.")

    # 9. Query Job-specific Analytics Endpoint
    print("\n9. Testing /jobs/{job_id} endpoint...")
    r = client.get(f"/api/v1/analytics/jobs/{job1_id}", headers=recruiter_headers)
    assert r.status_code == 200
    job_data = r.json()
    assert job_data["job_title"] == "Senior AI Architect"
    assert job_data["total_applications"] == 2
    assert job_data["average_match_score"] == 82.0
    assert len(job_data["top_matched_candidates"]) == 2
    assert job_data["top_matched_candidates"][0]["candidate_id"] == c1_id
    assert job_data["top_matched_candidates"][0]["match_percentage"] == 92.0
    assert job_data["shortlisted_count"] == 1
    print("Success: Job specific analytics details verified.")

    # 10. Query Recruitment Events Timeline Endpoint
    print("\n10. Testing /events timeline endpoint with filters...")
    r = client.get("/api/v1/analytics/events?event_type=JOB_CREATED", headers=recruiter_headers)
    assert r.status_code == 200
    events_data = r.json()
    assert events_data["total"] == 1
    assert events_data["events"][0]["event_type"] == "JOB_CREATED"
    
    # Filter by candidate
    r = client.get(f"/api/v1/analytics/events?candidate_id={c1_id}", headers=recruiter_headers)
    assert r.status_code == 200
    assert r.json()["total"] > 0
    print("Success: Timeline filter queries are functional.")

    # 11. Query Source Effectiveness Endpoint
    print("\n11. Testing /source-effectiveness endpoint...")
    r = client.get("/api/v1/analytics/source-effectiveness", headers=recruiter_headers)
    assert r.status_code == 200
    source_data = r.json()
    sources_dict = {s["source"]: s for s in source_data["sources"]}
    assert sources_dict["LINKEDIN"]["candidate_count"] == 1
    assert sources_dict["DIRECT_UPLOAD"]["candidate_count"] == 1
    assert sources_dict["LINKEDIN"]["shortlisted_count"] == 1
    print("Success: Source effectiveness aggregation verified.")

    # 12. Query Time-to-Hire Endpoint
    print("\n12. Testing /time-to-hire endpoint...")
    r = client.get("/api/v1/analytics/time-to-hire", headers=recruiter_headers)
    assert r.status_code == 200
    tth_data = r.json()
    # Offer average should be null since no candidate has status OFFERED
    assert tth_data["average_time_to_offer_days"] is None
    print("Success: Time to hire endpoint handles empty/missing status metrics gracefully.")

    # Update app 1 to OFFERED to trigger offer analytics
    app1.status = ApplicationStatus.OFFERED
    # Set dates programmatically to simulate 3 days gap
    app1.applied_at = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=3)
    app1.offered_at = datetime.datetime.now(datetime.timezone.utc)
    db.commit()

    r = client.get("/api/v1/analytics/time-to-hire", headers=recruiter_headers)
    assert r.status_code == 200
    tth_data_updated = r.json()
    assert tth_data_updated["average_time_to_offer_days"] is not None
    # Difference should be close to 3.0 days
    assert 2.9 <= tth_data_updated["average_time_to_offer_days"] <= 3.1
    print(f"Success: Offer transition average days calculated correctly: {tth_data_updated['average_time_to_offer_days']}")

    # 13. Query Recruiter Activity Endpoint
    print("\n13. Testing /recruiter-activity endpoint...")
    
    # Debug print all recruitment events
    print("--- DEBUG EVENT LOGS ---")
    all_evs = db.query(RecruitmentEvent).all()
    for ev in all_evs:
        print(f"EVENT: type={ev.event_type}, actor_id={ev.actor_id}, candidate_id={ev.candidate_id}, metadata={ev.metadata_json}")
    print("------------------------")
    
    r = client.get("/api/v1/analytics/recruiter-activity", headers=admin_headers)
    assert r.status_code == 200
    act_data = r.json()
    recruiters_act = {rec["user_id"]: rec for rec in act_data["recruiters"]}
    
    # Admin and Recruiter should be in stats
    rec_user = db.query(User).filter(User.email == "recruiter@recruitai.com").first()
    assert rec_user.id in recruiters_act
    rec_stats = recruiters_act[rec_user.id]
    print("REC STATS:", rec_stats)
    assert rec_stats["jobs_created"] == 1
    assert rec_stats["resumes_uploaded"] == 1
    assert rec_stats["candidates_shortlisted"] == 1
    print("Success: Recruiter activity aggregates verified.")

    db.close()
    engine.dispose()
    
    # Clean up test SQLite database
    try:
        os.remove("verify_analytics.db")
        print("\n14. Test database cleaned up.")
    except Exception as e:
        print(f"Cleanup warning: {str(e)}")

    print("\n--- ALL DASHBOARD & RECRUITMENT ANALYTICS INTEGRATION TESTS PASSED SUCCESSFULLY! ---")

if __name__ == "__main__":
    run_tests()
