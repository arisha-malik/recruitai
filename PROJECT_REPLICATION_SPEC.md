# Project Replication Specification: RecruitAI (AATA)

## 1. Project Overview

**Project Name:** RecruitAI (also referred to as AATA)
**Purpose of the platform:** An AI-powered recruitment platform that automates resume parsing, candidate profiling, job description generation, candidate-job matching, and interview question generation.
**Target Users:** Recruiters, Hiring Managers, and Interviewers.
**Main recruitment problem it solves:** The time-consuming manual processes of screening resumes, shortlisting candidates, aligning candidate skills with job requirements, and creating tailored interview questions.

**Current MVP Scope & Implemented Features:**
- User Authentication (Signup/Login/JWT).
- Resume Upload (Single and Mock S3 fallback).
- AI Resume Parsing (using Gemini LLM via Celery background tasks).
- Candidate Profile generation with skills, experience, and education tracking.
- Job creation and JD Generation (AI-driven).
- Candidate Matching Engine (Heuristic + LLM evaluation, optional Qdrant vector search).
- Interview Round tracking (Shortlisting, Rejecting, Maybe).
- Interview Assistant (AI generation of HR and Technical questions).
- Dashboard Analytics (Candidate counts, matching stats).

**Features Partially Implemented:**
- Bulk Resume Upload (Supported via iterating singles, but dedicated bulk UI might need refinement).
- Full RBAC (Roles exist in DB, but granular permission enforcement across all endpoints may not be strict).
- Qdrant Vector Search (Implemented in backend but disabled by default).

**Features Not Yet Implemented:**
- Real-time notification system.
- Direct email integration to candidates.
- Calendar integration for interview scheduling.

---

## 2. Tech Stack

- **Frontend Framework:** Next.js 14, React 19
- **Backend Framework:** FastAPI (Python 3)
- **Database:** PostgreSQL
- **ORM:** SQLAlchemy (v2)
- **Migration Tool:** Alembic
- **Authentication Method:** JWT (JSON Web Tokens) with passlib/bcrypt
- **AI Model/Provider:** Google Gemini (default: gemini-1.5-flash for parsing/generation, text-embedding-004 for embeddings)
- **Background Job System:** Celery with Redis broker (local dev fallback available via RUN_JOBS_SYNC)
- **File Storage Approach:** Local file system (mock S3) / AWS S3
- **Styling/UI Libraries:** Tailwind CSS (v4)
- **Icon Library:** Lucide React
- **Other important packages:** 
  - `pdfplumber`, `python-docx` (Text extraction)
  - `qdrant-client` (Vector DB)
  - `boto3` (AWS S3)

---

## 3. Folder Structure

```
AATA/
├── backend/
│   ├── app/
│   │   ├── models/        # SQLAlchemy Database Models (candidate.py, job.py, user.py, etc.)
│   │   ├── routers/       # FastAPI Route Controllers (auth.py, resumes.py, jobs.py, matching.py, etc.)
│   │   ├── schemas/       # Pydantic Schemas for Request/Response validation
│   │   ├── services/      # Core business logic (llm_service.py, matching_service.py, qdrant_service.py, etc.)
│   │   ├── worker/        # Celery App and Tasks (celery_app.py, tasks.py)
│   │   ├── config.py      # Environment variables configuration
│   │   ├── database.py    # DB connection setup
│   │   ├── dependencies.py# FastAPI dependencies (auth checks, db sessions)
│   │   └── main.py        # FastAPI application entry point
│   ├── migrations/        # Alembic migration scripts
│   ├── uploads/           # Local storage for mock S3 uploads
│   ├── requirements.txt   # Python dependencies
│   ├── alembic.ini        # Alembic configuration
│   └── .env               # Backend Environment variables
└── frontend/
    ├── src/
    │   ├── app/           # Next.js App Router (pages: login, dashboard, jobs, candidates, etc.)
    │   │   ├── (dashboard)/ # Authenticated layouts and routes
    │   │   └── globals.css  # Tailwind entry point
    │   ├── components/    # Reusable React components (Navbar, Sidebar, ui/Card, ui/Table, etc.)
    │   └── lib/           # Utility functions and API clients (axios setup)
    ├── public/            # Static assets
    ├── package.json       # Node dependencies and scripts
    ├── next.config.ts     # Next.js configuration
    └── tailwind.config.ts # Tailwind CSS config
```

---

## 4. Environment Setup

**Required Software:** Python 3.10+, Node.js 20+, PostgreSQL, Redis Server.

**Backend Setup:**
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
# Create PostgreSQL Database 'recruitai'
alembic upgrade head
python -m uvicorn app.main:app --reload
```

**Celery Worker Setup (Windows Note):**
```powershell
cd backend
.\.venv\Scripts\activate
celery -A app.worker.celery_app worker --loglevel=info --pool=solo
```

**Frontend Setup:**
```powershell
cd frontend
npm install
npm run dev
```

---

## 5. Environment Variables

**Backend (`backend/.env`):**
- `DATABASE_URL`: Required. Connection string. Example: `postgresql://postgres:pass@localhost:5432/recruitai`
- `JWT_SECRET_KEY`: Required. Secret for signing tokens. Example: `your_secret_key`
- `JWT_ALGORITHM`: Required. Example: `HS256`
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Required. Example: `1440`
- `REDIS_URL`: Required if Celery is used. Example: `redis://localhost:6379/0`
- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, `AWS_S3_BUCKET`: Optional for local, required for S3.
- `LLM_PROVIDER`: Required. Example: `gemini`
- `GEMINI_MODEL`: Required. Example: `gemini-1.5-flash`
- `EMBEDDING_PROVIDER`: Required. Example: `gemini`
- `GEMINI_API_KEY`: Required. Example: `AIza...`
- `STORAGE_MODE`: Required. Example: `local`
- `RUN_JOBS_SYNC`: Required. True to bypass Celery for local testing. Example: `false`
- `QDRANT_ENABLED`: Optional. Example: `false`
- `MATCHING_TOP_N`: Optional. Example: `20`

**Frontend (`frontend/.env.local`):**
- `NEXT_PUBLIC_API_URL`: Required. Example: `http://localhost:8000/api/v1`

---

## 6. Database Design

**1. `users`:**
- `id` (String PK), `email` (String UK), `password_hash` (String), `first_name`, `last_name`, `role` (Enum: ADMIN, RECRUITER, etc.).

**2. `candidates`:**
- `id` (String PK), `first_name`, `last_name`, `email`, `phone`, `current_company`, `current_location`, `total_experience_years`, `skills` (JSON), `source`.

**3. `resumes`:**
- `id` (String PK), `candidate_id` (FK), `file_name`, `s3_key`, `s3_bucket`, `parsing_status` (Enum: UPLOADED, PARSING, PARSED, FAILED), `raw_text`, `failure_reason`.

**4. `parsed_resume_data`:**
- Detailed fields generated by LLM (JSON for arrays like education, work_experience, projects, etc.).

**5. `jobs`:**
- `id` (String PK), `title`, `department`, `location`, `employment_type`, `experience_level`, `description`, `required_skills` (JSON), `status`, `created_by_id`, `embedding_status`, `matching_status`.

**6. `applications`:**
- `id` (String PK), `candidate_id` (FK), `job_id` (FK), `status` (Enum: APPLIED, PARSING, MATCHED, SHORTLISTED, REJECTED, etc.).

**7. `match_results`:**
- `id` (String PK), `candidate_id`, `job_id`, `application_id`, `match_percentage`, `skill_match_analysis`, `matched_skills`, `missing_skills`, `experience_analysis`, `final_recommendation`, `raw_llm_response`.

**8. `generated_job_descriptions` & `generated_interview_questions`:** Stores AI prompts and JSON outputs.
**9. `recruitment_events` & `audit_logs`:** For timeline/audit trails.

---

## 7. Backend API Documentation

*(All routes prefixed with `/api/v1`)*

- **Auth**
  - `POST /auth/signup`: Create user.
  - `POST /auth/login`: Authenticate and return JWT token.
  - `GET /auth/me`: Get current user info.
- **Resumes**
  - `POST /uploads/`: Upload resume.
  - `POST /uploads/mock-s3-upload`: Upload to local storage for dev.
  - `GET /resumes/{id}`: Get parse status and data.
- **Candidates**
  - `GET /candidates/`: List candidates.
  - `PATCH /candidates/{id}`: Update profile.
  - `DELETE /candidates/{id}`: Delete profile.
- **Jobs**
  - `GET /jobs/`: List jobs.
  - `POST /jobs/`: Create job.
  - `PATCH /jobs/{id}`: Update job status.
- **Matching**
  - `POST /matching/job/{job_id}/run`: Trigger candidate matching task.
  - `GET /matching/job/{job_id}/results`: View match scores and reasoning.
- **Applications/Interview**
  - `PATCH /applications/{id}/status`: Shortlist, reject, maybe.
- **Assistant**
  - `POST /assistant/generate-jd`: Use LLM to generate Job Description.
  - `POST /assistant/generate-interview-questions`: Use LLM to generate questions based on candidate profile.
- **Analytics**
  - `GET /analytics/dashboard`: General platform stats.

---

## 8. Authentication and RBAC

- **Flow:** User POSTs email/pass to `/auth/login`. Returns JWT (`access_token`). Frontend stores token (usually localStorage/cookies) and attaches `Authorization: Bearer <token>` to requests.
- **Roles:** Defined in Enum (`ADMIN`, `RECRUITER`, `HIRING_MANAGER`, `INTERVIEWER`).
- **RBAC Limitations:** Endpoints utilize `get_current_user` dependency, but strict role enforcement per-route (e.g., only Admin can delete jobs) might require explicit dependency validation (`get_admin_user` etc.).

---

## 9. Resume Upload and Parsing Flow

1. Recruiter uploads PDF/DOCX via UI.
2. Hit `POST /uploads/mock-s3-upload` (Local mode) -> Saved to `/uploads`.
3. Resume and temporary Candidate records created. Parsing status = `UPLOADED`.
4. Celery Task `parse_resume_job` is dispatched.
5. **Background:** Task reads file, extracts text, sends to Gemini LLM for structured extraction.
6. Updates `parsed_resume_data` and merges data into `Candidate` record.
7. Generates Qdrant embeddings (if enabled). Status = `PARSED`.
8. Frontend polls or refreshes to see parsed candidate profile.

---

## 10. Candidate Profile Feature

- **List Page:** Shows parsed candidates with skills badges, experience, location.
- **Profile Page:** Detailed view mapping `parsed_resume_data`. Expandable sections for Work Experience, Education, and Projects.
- **Delete Behavior:** Deleting a candidate cascades to resumes, applications, and match results.

---

## 11. Job Description / Jobs Feature

- **Creation:** Recruiter inputs basic title, department, location. Can hit "Generate with AI" which calls `/assistant/generate-jd` to populate the rich text description and required skills.
- **Storage:** Stored in `jobs` table with `status=DRAFT|OPEN`.
- **Linking:** Acts as the anchor for the Matching Engine.

---

## 12. Candidate Matching Flow

1. Job is created and set to `OPEN`.
2. Recruiter clicks "Run Matching" -> Triggers Celery task `run_candidate_matching_job`.
3. **Filtering:** System optionally fetches top N from Qdrant vector search. If Qdrant is disabled, fetches candidates and ranks using a heuristic scoring logic (skills overlap + experience match + location match).
4. **LLM Evaluation:** Passes Top N candidates + Job Description to Gemini. Gemini outputs `match_percentage`, missing skills, strengths, and a `final_recommendation` (SHORTLIST, REJECT, MAYBE).
5. **UI Display:** Candidates shown ranked by score with colored badges for recommendations.
6. **Actions:** Recruiter can override or accept recommendations to move candidate to Interview Round.

---

## 13. Interview Round Flow

- Once an application status is changed to `SHORTLISTED` or `INTERVIEWING`, they appear in the Interview Round section.
- Recruiter tracks progress (e.g., move to `OFFERED` or `REJECTED`).
- From this view, the recruiter can launch the Interview Assistant.

---

## 14. Interview Assistant

- Available on shortlisted candidates.
- Triggers `/assistant/generate-interview-questions`.
- Takes the Job Description, Candidate Skills, and requested Level (Junior, Mid, Senior) & Type (HR, Tech).
- LLM outputs structured JSON array of questions tailored specifically to verify the candidate's claims against the job needs.
- Displayed in UI as cards/accordions.

---

## 15. Dashboard and Analytics

- Summary Cards: Total Candidates, Open Jobs, Resumes Parsed, Successful Matches.
- Charts/Metrics rely on PostgreSQL aggregations (e.g., grouping applications by status).
- *Note:* Depending on current data populations, some visual charts might use mock data wrappers in the frontend until enough real data is generated.

---

## 16. Frontend UI Documentation

- **Theme:** Minimalist, modern enterprise. High contrast dark mode or clean light mode using Tailwind CSS.
- **Navigation:** Left sidebar (Dashboard, Candidates, Jobs, Analytics) and Top header (User Profile).
- **Components:** Uses highly reusable Lucide React icons, custom Badges (`StatusBadge.tsx`, `MatchScoreBadge.tsx`), and unified `Card` components for layout.
- **State Handling:** `LoadingState.tsx` and `ErrorState.tsx` provide standardized UX for async API calls.

---

## 17. Background Jobs / Celery

- **Tasks:** `parse_resume_job` (Resume extraction), `run_candidate_matching_job` (AI Matching).
- **Location:** `backend/app/worker/tasks.py`.
- **Fallback:** Setting `RUN_JOBS_SYNC=True` runs these synchronously in the main thread (useful for Windows local dev without setting up Redis/Celery).

---

## 18. AI Integration

- **Provider:** Google Gemini API.
- **Prompts:** Hardcoded system prompts in `llm_service.py` and `matching_service.py` demanding strict JSON output schema.
- **Embeddings:** `text-embedding-004` used to convert candidate profiles into vectors for Qdrant similarity searches (currently an optional enhancement).
- **Error Handling:** Built-in retries for rate limits and `LLMParsingError` definitions for malformed JSON returns.

---

## 19. Current Known Bugs / Broken Areas

- **Qdrant Initialization:** If `QDRANT_ENABLED=true` but the Qdrant server is down, matching jobs may fail completely rather than gracefully falling back to DB heuristic search.
- **Frontend Fallbacks:** If a resume is heavily formatted and parsing fails entirely, the UI might stay in "Parsing" state indefinitely without polling timeout mechanisms.
- **Role Enforcement:** Advanced RBAC (e.g. limiting an interviewer from deleting a job) requires code audit across all routers; currently, most routes just check if the user is authenticated.
- **Email Merge Edge Case:** If the LLM hallucinates an email or extracts a recruiter's email from a resume, it might improperly merge candidate profiles.

---

## 20. Feature Completion Checklist

- [x] Authentication
- [x] Resume upload (Single)
- [x] Resume parsing (AI)
- [x] Candidate profile creation
- [x] Candidate search/filtering
- [x] Candidate delete
- [x] JD generation (AI)
- [x] Job creation
- [x] Candidate matching (AI/Heuristic)
- [x] Candidate ranking/scoring
- [x] Shortlist/reject/maybe
- [x] Interview question generation (AI)
- [x] Dashboard analytics
- [ ] Bulk resume upload (UI Support needs polish)
- [ ] Strict RBAC route guards
- [ ] Direct Email / Calendar integrations

---

## 21. End-to-End User Flows

**Flow: Resume to Interview**
1. **Recruiter logs in** (UI -> `POST /auth/login` -> token stored).
2. **Uploads Resume** (UI -> `POST /uploads/mock-s3-upload` -> `UPLOADED` state).
3. **Parsing** (Celery picks up task -> extracts text -> calls Gemini -> updates DB -> `PARSED` state).
4. **Create Job** (Recruiter fills job form, clicks "Generate JD" -> Gemini creates description -> saves to DB).
5. **Run Matching** (Recruiter clicks "Match" -> Celery evaluates candidates against Job -> DB populated with `MatchResult`).
6. **Shortlist** (Recruiter reviews scores, changes status to `SHORTLISTED` -> application updated).
7. **Interview Prep** (Recruiter generates Technical questions using Interview Assistant -> Gemini creates questions -> displayed).

---

## 22. Testing Guide

1. Start Postgres and Redis.
2. Start backend (`uvicorn app.main:app --reload`), Celery worker, and frontend (`npm run dev`).
3. Open `http://localhost:3000/login` -> create a test user.
4. Go to **Candidates** -> Upload a PDF resume. Wait 10-15 seconds and refresh to see it parsed.
5. Go to **Jobs** -> Create Job -> use AI to generate the description -> Save.
6. In Job Details, click **Run Matching**. Wait for Celery to finish.
7. Review matched candidates -> Move one to Shortlist.
8. View the candidate -> Generate Interview Questions.

---

## 23. Exact Replication Notes

To replicate this project exactly, developers must ensure:
1. **Prompts:** The specific JSON schemas and prompts inside `llm_service.py` and `matching_service.py` must be identical to guarantee the UI renders tables and badges correctly.
2. **Postgres & Celery:** The async architecture is non-negotiable for file processing and AI timeouts.
3. **Environment:** Gemini API keys must have access to `gemini-1.5-flash` at minimum.
4. **Data Models:** The SQLAlchemy schema defines the exact JSON structure expected by the Next.js frontend; modifications to the DB require parallel TypeScript interface updates.
