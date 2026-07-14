import os
import shutil
import tempfile
import logging
from typing import Optional
from celery import Task
from celery.exceptions import MaxRetriesExceededError
from sqlalchemy.orm import Session

from app.worker.celery_app import celery_app
from app.database import SessionLocal
from app.config import settings
from app.models.candidate import Resume, Candidate, ParsedResumeData, ParsingStatus
from app.models.job import Job, JobEmbeddingStatus, MatchingStatus
from app.models.application import MatchResult, Application, ApplicationStatus
from app.services.text_extraction_service import extract_text_from_file
from app.services.domain_service import normalize_candidate_domain
from app.services.llm_service import LLMService, LLMParsingError
from app.services.embedding_service import EmbeddingService, build_candidate_profile_summary, build_job_profile_summary
from app.services.qdrant_service import QdrantService
from app.services.matching_service import MatchingLLMService, MatchingLLMError
from app.services.event_service import log_recruitment_event

logger = logging.getLogger(__name__)

def download_resume_file(bucket: str, key: str, temp_file_path: str) -> None:
    """
    Downloads file from actual S3 bucket or copies it from mock local path.
    """
    # 1. Standard S3 Client Download
    if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
        try:
            import boto3
            s3 = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION
            )
            logger.info(f"Downloading file from S3: bucket={bucket}, key={key}...")
            s3.download_file(bucket, key, temp_file_path)
            logger.info("S3 file download complete.")
            return
        except Exception as e:
            logger.warning(f"S3 download failed, checking local mock fallback: {str(e)}")
            
    # 2. Local mock fallback (checks if uploads folder has the file)
    base_uploads_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "uploads"))
    local_path = os.path.join(base_uploads_dir, key)
    if os.path.exists(local_path):
        logger.info(f"Mock S3: copying file from local path {local_path}...")
        shutil.copy2(local_path, temp_file_path)
        return
        
    raise FileNotFoundError(f"Resume file could not be retrieved from S3 or local mock directory: key={key}")

@celery_app.task(bind=True, max_retries=3, default_retry_delay=15)
def parse_resume_job(self, resume_id: str, actor_id: Optional[str] = None):
    """
    Background job to parse resume text using LLM, populate database schemas,
    generate candidates' embedding vectors, and index them in Qdrant.
    """
    logger.info(f"Starting resume parsing task: resume_id={resume_id}")
    
    db: Session = SessionLocal()
    temp_file_path = None
    
    try:
        # 1. Fetch Resume & Candidate
        resume = db.query(Resume).filter(Resume.id == resume_id).first()
        if not resume:
            logger.error(f"Resume record not found: {resume_id}")
            return
            
        candidate = db.query(Candidate).filter(Candidate.id == resume.candidate_id).first()
        if not candidate:
            logger.error(f"Candidate profile not found: {resume.candidate_id}")
            return
            
        # 2. Update status and log parsing started event
        resume.parsing_status = ParsingStatus.PARSING
        db.commit()
        
        # Check for existing event to avoid duplicate logs on task retries
        from app.models.audit import RecruitmentEvent
        existing_event = db.query(RecruitmentEvent).filter(
            RecruitmentEvent.resume_id == resume.id,
            RecruitmentEvent.event_type == "RESUME_PARSING_STARTED"
        ).first()
        
        if not existing_event:
            log_recruitment_event(
                db=db,
                event_type="RESUME_PARSING_STARTED",
                candidate_id=candidate.id,
                resume_id=resume.id,
                actor_id=actor_id,
                metadata={"filename": resume.file_name}
            )
        
        # 3. Create temp file and download content
        temp_dir = tempfile.gettempdir()
        file_ext = os.path.splitext(resume.file_name.lower())[1]
        temp_file_path = os.path.join(temp_dir, f"{resume_id}{file_ext}")
        
        download_resume_file(resume.s3_bucket, resume.s3_key, temp_file_path)
        
        # 4. Extract Text
        logger.info(f"Extracting text from resume {resume.file_name}...")
        extracted_text = extract_text_from_file(temp_file_path, resume.file_name)
        
        # Save raw extracted text to DB
        resume.raw_text = extracted_text
        db.commit()
        
        # 5. Invoke LLM Parsing Service
        logger.info("Parsing resume text using LLM service...")
        llm_service = LLMService()
        parsed_data = llm_service.parse_resume_text(extracted_text)
        
        # 6. Store Parsed Data in Postgres
        parsed_resume_entry = db.query(ParsedResumeData).filter(ParsedResumeData.resume_id == resume_id).first()
        if not parsed_resume_entry:
            import uuid
            parsed_resume_entry = ParsedResumeData(
                id=str(uuid.uuid4()),
                resume_id=resume_id
            )
            db.add(parsed_resume_entry)
            
        parsed_resume_entry.full_name = parsed_data.get("full_name")
        parsed_resume_entry.email = parsed_data.get("email")
        parsed_resume_entry.mobile_number = parsed_data.get("mobile_number")
        parsed_resume_entry.total_experience_years = parsed_data.get("total_experience_years")
        parsed_resume_entry.total_experience = parsed_data.get("total_experience_years") # sync both
        parsed_resume_entry.technical_skills = parsed_data.get("technical_skills")
        parsed_resume_entry.education = parsed_data.get("education")
        parsed_resume_entry.certifications = parsed_data.get("certifications")
        parsed_resume_entry.current_company = parsed_data.get("current_company")
        parsed_resume_entry.current_location = parsed_data.get("current_location")
        parsed_resume_entry.notice_period = parsed_data.get("notice_period")
        parsed_resume_entry.work_experience = parsed_data.get("work_experience")
        parsed_resume_entry.projects = parsed_data.get("projects")
        parsed_resume_entry.raw_json = parsed_data
        
        # 7. Update Candidate profile columns without overwriting manual updates
        
        parsed_email = parsed_data.get("email")
        if candidate.email.startswith("pending-") and parsed_email:
            # Check if this email belongs to an EXISTING candidate
            existing_candidate = db.query(Candidate).filter(Candidate.email == parsed_email).first()
            if existing_candidate and existing_candidate.id != candidate.id:
                # Merge: Move this resume to the existing candidate
                logger.info(f"Merging temporary candidate {candidate.id} into existing {existing_candidate.id}")
                resume.candidate_id = existing_candidate.id
                db.commit()
                # Delete the temporary placeholder candidate
                db.delete(candidate)
                db.commit()
                candidate = existing_candidate
            else:
                candidate.email = parsed_email
                
        # Check first and last name parsing
        if (not candidate.first_name or candidate.first_name in ["Candidate", "Pending"]) and parsed_data.get("full_name"):
            names = parsed_data["full_name"].strip().split(" ", 1)
            candidate.first_name = names[0]
            if len(names) > 1:
                candidate.last_name = names[1]
                
        if not candidate.phone and parsed_data.get("mobile_number"):
            candidate.phone = parsed_data["mobile_number"]
            
        if not candidate.current_company and parsed_data.get("current_company"):
            candidate.current_company = parsed_data["current_company"]
            
        if not candidate.current_location and parsed_data.get("current_location"):
            candidate.current_location = parsed_data["current_location"]
            
        if (candidate.total_experience_years is None or candidate.total_experience_years == 0.0) and parsed_data.get("total_experience_years"):
            candidate.total_experience_years = parsed_data["total_experience_years"]
            
        if not candidate.notice_period and parsed_data.get("notice_period"):
            candidate.notice_period = parsed_data["notice_period"]
            
        if not candidate.education_level and parsed_data.get("education"):
            edu_str = str(parsed_data["education"]).lower()
            if "phd" in edu_str or "doctor" in edu_str:
                candidate.education_level = "PhD"
            elif "master" in edu_str or "m.sc" in edu_str or "mba" in edu_str:
                candidate.education_level = "Master's"
            elif "bachelor" in edu_str or "b.sc" in edu_str or "b.tech" in edu_str or "b.e" in edu_str:
                candidate.education_level = "Bachelor's"
            else:
                candidate.education_level = "Other"
                
        # Merge skills list (taking union to preserve existing + add parsed)
        existing_skills = set(candidate.skills or [])
        parsed_skills = set(parsed_data.get("technical_skills") or [])
        candidate.skills = sorted(list(existing_skills.union(parsed_skills)))
        
        if not candidate.domain:
            candidate.domain = normalize_candidate_domain(
                title=candidate.current_company,
                skills=candidate.skills,
                education=candidate.education_level,
                text=extracted_text
            )

        db.commit()
        
        # Log parsed success event
        log_recruitment_event(
            db=db,
            event_type="RESUME_PARSED",
            candidate_id=candidate.id,
            resume_id=resume.id,
            actor_id=actor_id,
            metadata={"parsed_name": parsed_data.get("full_name")}
        )
        
        # 8. Generate Vector Embedding and Upsert to Qdrant
        if settings.QDRANT_ENABLED:
            logger.info("Generating candidate profile summary and vector embedding...")
            embedding_service = EmbeddingService()
            
            # Construct summary string for embedding representation
            profile_summary = build_candidate_profile_summary(parsed_data)
            
            try:
                vector = embedding_service.generate_embedding(profile_summary)
                
                # Upsert vector into Qdrant index
                logger.info("Upserting vector embedding into Qdrant collection...")
                qdrant_service = QdrantService()
                qdrant_service.upsert_candidate_vector(
                    candidate_id=candidate.id,
                    resume_id=resume.id,
                    vector=vector,
                    skills=candidate.skills,
                    experience_years=candidate.total_experience_years,
                    location=candidate.current_location,
                    current_company=candidate.current_company,
                    domain=candidate.domain
                )
                
                log_recruitment_event(
                    db=db,
                    event_type="CANDIDATE_VECTOR_CREATED",
                    candidate_id=candidate.id,
                    resume_id=resume.id,
                    actor_id=actor_id
                )
            except Exception as vec_err:
                logger.error(f"Vector creation failed: {str(vec_err)}")
                log_recruitment_event(
                    db=db,
                    event_type="CANDIDATE_VECTOR_FAILED",
                    candidate_id=candidate.id,
                    resume_id=resume.id,
                    actor_id=actor_id,
                    metadata={"error": str(vec_err)}
                )
                # We don't fail the whole parse if only Qdrant indexing failed,
                # but we raise to retry if Qdrant is critical. Let's raise here so Celery retries.
                raise vec_err
        else:
            logger.info("Qdrant is disabled. Skipping vector embedding generation and Qdrant upsert.")
            
        # 9. Rename and move file to final storage path
        import re
        
        raw_name = parsed_data.get("full_name") or f"{candidate.first_name} {candidate.last_name}".strip()
        if not raw_name or raw_name.lower() in ["candidate", "pending"]:
            raw_name = "candidate"
            
        designation = None
        work_exp = parsed_data.get("work_experience") or []
        if work_exp and isinstance(work_exp, list) and len(work_exp) > 0:
            if isinstance(work_exp[0], dict) and work_exp[0].get("role"):
                designation = work_exp[0].get("role")
            elif isinstance(work_exp[0], dict) and work_exp[0].get("title"):
                designation = work_exp[0].get("title")
                
        if not designation:
            designation = candidate.current_company
            
        if not designation and candidate.skills and len(candidate.skills) > 0:
            designation = candidate.skills[0]
            
        if not designation:
            designation = candidate.domain or "tech-candidate"
            
        def sanitize_filename(s):
            if not s: return "unknown"
            s = str(s).lower()
            s = re.sub(r'[^a-z0-9\s-]', '', s)
            s = re.sub(r'[\s]+', '-', s)
            return s.strip('-')
            
        sanitized_name = sanitize_filename(raw_name)
        sanitized_role = sanitize_filename(designation)
        short_id = resume.id.split('-')[0]
        ext = os.path.splitext(resume.file_name)[1].lower()
        
        stored_filename = f"{sanitized_name}_{sanitized_role}_{short_id}{ext}"
        candidate_field = sanitize_filename(candidate.domain or "uncategorized")
        
        new_s3_key = f"{settings.S3_PREFIX}Resume/{stored_filename}"
        
        try:
            from app.services.s3_service import move_s3_object
            move_s3_object(resume.s3_bucket, resume.s3_key, new_s3_key)
            
            resume.stored_filename = stored_filename
            resume.storage_path = new_s3_key
            resume.s3_key = new_s3_key
            resume.candidate_primary_designation = designation
            resume.primary_skill = candidate.skills[0] if candidate.skills else None
            resume.candidate_field = candidate.domain
            
            skills_str = " ".join(candidate.skills) if candidate.skills else ""
            search_lbl = f"{raw_name} {designation} {skills_str} {candidate.domain}".lower()
            resume.searchable_storage_label = re.sub(r'[\s]+', ' ', search_lbl).strip()
            
            log_recruitment_event(
                db=db,
                event_type="RESUME_MOVED",
                candidate_id=candidate.id,
                resume_id=resume.id,
                actor_id=actor_id,
                metadata={"new_path": new_s3_key}
            )
        except Exception as move_err:
            logger.error(f"Failed to move resume file to final path: {str(move_err)}")
            log_recruitment_event(
                db=db,
                event_type="RESUME_MOVE_FAILED",
                candidate_id=candidate.id,
                resume_id=resume.id,
                actor_id=actor_id,
                metadata={"error": str(move_err)}
            )

        # 10. Mark resume parsing status as successful
        resume.parsing_status = ParsingStatus.PARSED
        resume.failure_reason = None
        db.commit()
        logger.info(f"Resume parsing job completed successfully: resume_id={resume_id}")
        
    except Exception as exc:
        logger.error(f"Error in parse_resume_job: {str(exc)}")
        db.rollback()
        
        # Determine if we should retry (e.g. on external API rate-limit errors or transient Qdrant failures)
        # We retry unless it's a structural parsing error or file support issue
        is_transient = isinstance(exc, (LLMParsingError, ConnectionError, Exception))
        
        if is_transient and self.request.retries < self.max_retries:
            logger.info(f"Retrying task: retry {self.request.retries + 1}/{self.max_retries}...")
            try:
                self.retry(exc=exc)
            except MaxRetriesExceededError:
                pass # fall through to final failure
            else:
                return # task successfully scheduled for retry
                
        # Final failure operations
        try:
            resume = db.query(Resume).filter(Resume.id == resume_id).first()
            if resume:
                resume.parsing_status = ParsingStatus.FAILED
                resume.failure_reason = str(exc)
                db.commit()
                
                log_recruitment_event(
                    db=db,
                    event_type="RESUME_PARSING_FAILED",
                    candidate_id=resume.candidate_id,
                    resume_id=resume.id,
                    actor_id=actor_id,
                    metadata={"error": str(exc)}
                )
        except Exception as db_err:
            logger.critical(f"Failed to record final parsing failure status in DB: {str(db_err)}")
            
    finally:
        # Clean up temporary downloaded file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
                logger.info(f"Cleaned up temporary file: {temp_file_path}")
            except Exception as e:
                logger.warning(f"Failed to delete temp file {temp_file_path}: {str(e)}")
                
        db.close()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=15)
def run_candidate_matching_job(self, job_id: str, actor_id: Optional[str] = None):
    """
    Background job to run the AI candidate matching pipeline for a job.
    1. Generates job description embedding if not generated.
    2. Searches Qdrant candidates_vectors collection for similar candidates.
    3. Triggers the LLM matching evaluation for retrieved candidates.
    4. Persists results and updates status.
    """
    logger.info(f"Starting candidate matching job: job_id={job_id}")
    db: Session = SessionLocal()
    
    try:
        # 1. Fetch Job description
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            logger.error(f"Job record not found: {job_id}")
            return
            
        # 2. Update status and log matching started event
        job.matching_status = MatchingStatus.MATCHING
        job.matching_error = None
        db.commit()
        
        log_recruitment_event(
            db=db,
            event_type="MATCHING_STARTED",
            job_id=job.id,
            actor_id=actor_id
        )
        
        # 3. Generate Job description embedding if Qdrant is enabled
        job_vector = None
        job_data = {
            "title": job.title,
            "department": job.department,
            "location": job.location,
            "employment_type": job.employment_type,
            "experience_level": job.experience_level,
            "description": job.description,
            "required_skills": job.required_skills
        }
        
        if settings.QDRANT_ENABLED:
            embedding_service = EmbeddingService()
            logger.info(f"Generating embedding for job {job.title}...")
            job.embedding_status = JobEmbeddingStatus.EMBEDDING
            db.commit()
            
            try:
                job_summary = build_job_profile_summary(job_data)
                job_vector = embedding_service.generate_embedding(job_summary)
                job.embedding_status = JobEmbeddingStatus.EMBEDDED
                db.commit()
                
                log_recruitment_event(
                    db=db,
                    event_type="JOB_EMBEDDING_CREATED",
                    job_id=job.id,
                    actor_id=actor_id
                )
            except Exception as emb_err:
                job.embedding_status = JobEmbeddingStatus.FAILED
                db.commit()
                log_recruitment_event(
                    db=db,
                    event_type="JOB_EMBEDDING_FAILED",
                    job_id=job.id,
                    actor_id=actor_id,
                    metadata={"error": str(emb_err)}
                )
                raise emb_err
        else:
            logger.info("Qdrant is disabled. Skipping job embedding generation.")
            
        # 4. Search candidates
        top_n = settings.MATCHING_TOP_N
        candidates_hits = []
        
        if settings.QDRANT_ENABLED:
            logger.info(f"Querying Qdrant for top {top_n} candidates...")
            qdrant_service = QdrantService()
            try:
                candidates_hits = qdrant_service.search_candidates_vectors(
                    query_vector=job_vector,
                    top_n=top_n,
                    domain_filter=job.domain
                )
                logger.info(f"Qdrant returned {len(candidates_hits)} candidate matches.")
            except Exception as qd_err:
                logger.warning(f"Qdrant search failed, falling back to database query: {str(qd_err)}")
                db_candidates = db.query(Candidate).filter(Candidate.domain == job.domain).limit(top_n).all()
                candidates_hits = [{
                    "candidate_id": c.id,
                    "score": None,
                    "skills": c.skills,
                    "location": c.current_location,
                    "total_experience_years": c.total_experience_years
                } for c in db_candidates]
        else:
            # Basic Candidate Matching without Qdrant
            # We removed the hard database filters for location and experience.
            # Instead, we fetch all candidates and rely purely on the heuristic ranking 
            # (which assigns bonus points for location and experience matches) to bubble 
            # up the best candidates. This ensures candidates with great skills aren't 
            # strictly filtered out just because of a slight location or experience mismatch.
            query = db.query(Candidate).filter(Candidate.domain == job.domain)
            candidates_list = query.all()
            
            # Heuristic ranking in Python to choose top 10-20 candidates
            scored_candidates = []
            job_skills_set = set(s.lower() for s in (job.required_skills or []))
            
            for c in candidates_list:
                score = 0.0
                if c.skills and job_skills_set:
                    c_skills_set = set(s.lower() for s in c.skills)
                    overlap = len(c_skills_set.intersection(job_skills_set))
                    score += overlap * 10.0
                    
                if c.total_experience_years is not None:
                    if "senior" in (job.experience_level or "").lower():
                        if c.total_experience_years >= 5.0:
                            score += 15.0
                    elif "mid" in (job.experience_level or "").lower():
                        if 2.0 <= c.total_experience_years <= 5.0:
                            score += 15.0
                    else:
                        if c.total_experience_years <= 2.0:
                            score += 15.0
                            
                if job.location and c.current_location:
                    if job.location.lower() in c.current_location.lower() or c.current_location.lower() in job.location.lower():
                        score += 10.0
                        
                scored_candidates.append((score, c))
                
            scored_candidates.sort(key=lambda x: x[0], reverse=True)
            top_candidates = [c for _, c in scored_candidates[:top_n]]
            
            candidates_hits = [{
                "candidate_id": c.id,
                "score": None,
                "skills": c.skills,
                "location": c.current_location,
                "total_experience_years": c.total_experience_years
            } for c in top_candidates]
            
            logger.info(f"Filtered to top {len(candidates_hits)} candidates via DB filters & Python ranking heuristic.")
            
        # 5. Process matches
        matching_service = MatchingLLMService()
        total_checked = 0
        total_created = 0
        
        # PRE-FETCH BULK DATA TO PREVENT N+1 QUERIES
        from sqlalchemy.orm import joinedload
        candidate_ids = [hit["candidate_id"] for hit in candidates_hits] if candidates_hits else []
        
        candidate_dict = {}
        app_dict = {}
        match_dict = {}
        
        if candidate_ids:
            candidates = db.query(Candidate).options(
                joinedload(Candidate.resumes).joinedload(Resume.parsed_data)
            ).filter(Candidate.id.in_(candidate_ids)).all()
            candidate_dict = {c.id: c for c in candidates}
            
            apps = db.query(Application).filter(
                Application.job_id == job.id,
                Application.candidate_id.in_(candidate_ids)
            ).all()
            app_dict = {app.candidate_id: app for app in apps}
            
            matches = db.query(MatchResult).filter(
                MatchResult.job_id == job.id,
                MatchResult.candidate_id.in_(candidate_ids)
            ).all()
            match_dict = {m.candidate_id: m for m in matches}
        
        for hit in candidates_hits:
            candidate_id = hit["candidate_id"]
            vector_score = hit["score"]
            
            # Fetch Candidate and ParsedResumeData (from dictionary)
            candidate = candidate_dict.get(candidate_id)
            if not candidate:
                continue
                
            parsed_resume = None
            if candidate.resumes:
                for r in sorted(candidate.resumes, key=lambda x: x.created_at, reverse=True):
                    if r.parsed_data:
                        parsed_resume = r.parsed_data
                        break
            
            candidate_info = {
                "id": candidate.id,
                "first_name": candidate.first_name,
                "last_name": candidate.last_name,
                "total_experience_years": candidate.total_experience_years,
                "skills": candidate.skills or [],
                "current_location": candidate.current_location,
                "current_company": candidate.current_company,
                "notice_period": None,
                "work_experience": [],
                "projects": []
            }
            
            if parsed_resume:
                candidate_info.update({
                    "notice_period": parsed_resume.notice_period,
                    "work_experience": parsed_resume.work_experience or [],
                    "projects": parsed_resume.projects or []
                })
                
            total_checked += 1
            logger.info(f"Running LLM comparison for candidate: {candidate.first_name} {candidate.last_name}...")
            
            try:
                import time
                time.sleep(4.5) # Sleep to avoid 15 RPM rate limit
                eval_res = matching_service.evaluate_match(job_data, candidate_info)
                
                app = app_dict.get(candidate.id)
                if not app:
                    import uuid as uuid_lib
                    app = Application(
                        id=str(uuid_lib.uuid4()),
                        candidate_id=candidate.id,
                        job_id=job.id,
                        status=ApplicationStatus.MATCHED
                    )
                    db.add(app)
                    db.flush()
                app_id = app.id
                
                match_result = match_dict.get(candidate.id)
                
                is_new = match_result is None
                if is_new:
                    import uuid as uuid_lib
                    match_result = MatchResult(
                        id=str(uuid_lib.uuid4()),
                        candidate_id=candidate.id,
                        job_id=job.id,
                        application_id=app_id
                    )
                    db.add(match_result)
                    
                match_result.application_id = app_id
                match_result.vector_similarity_score = vector_score
                match_result.match_percentage = eval_res["match_percentage"]
                match_result.skill_match_analysis = eval_res["skill_match_analysis"]
                match_result.matched_skills = eval_res["matched_skills"]
                match_result.missing_skills = eval_res["missing_skills"]
                match_result.experience_analysis = eval_res["experience_analysis"]
                match_result.experience_delta = eval_res["experience_delta"]
                match_result.location_fit = eval_res["location_fit"]
                match_result.notice_period_fit = eval_res["notice_period_fit"]
                match_result.strengths = eval_res["strengths"]
                match_result.concerns = eval_res["concerns"]
                match_result.final_recommendation = eval_res["final_recommendation"]
                match_result.summary = eval_res["summary"]
                match_result.raw_llm_response = eval_res
                
                db.commit()
                total_created += 1
                
                log_recruitment_event(
                    db=db,
                    event_type="CANDIDATE_MATCH_CREATED" if is_new else "CANDIDATE_MATCH_UPDATED",
                    candidate_id=candidate.id,
                    job_id=job.id,
                    actor_id=actor_id,
                    metadata={"match_percentage": eval_res["match_percentage"]}
                )
                
            except Exception as eval_err:
                logger.error(f"Failed to match candidate {candidate.id}: {str(eval_err)}")
                raise eval_err
                
        job.total_candidates_checked = total_checked
        job.total_matches_created = total_created
        job.matching_status = MatchingStatus.COMPLETED
        db.commit()
        
        log_recruitment_event(
            db=db,
            event_type="MATCHING_COMPLETED",
            job_id=job.id,
            actor_id=actor_id,
            metadata={"checked": total_checked, "matched": total_created}
        )
        logger.info(f"Candidate matching completed: job_id={job_id}, matched={total_created}")
        
    except Exception as exc:
        logger.error(f"Error in run_candidate_matching_job: {str(exc)}")
        db.rollback()
        
        is_transient = isinstance(exc, (MatchingLLMError, ConnectionError, Exception))
        if is_transient and self.request.retries < self.max_retries and not settings.RUN_JOBS_SYNC:
            logger.info(f"Retrying task: retry {self.request.retries + 1}/{self.max_retries}...")
            try:
                self.retry(exc=exc)
            except MaxRetriesExceededError:
                pass
            else:
                return
                
        try:
            job = db.query(Job).filter(Job.id == job_id).first()
            if job:
                job.matching_status = MatchingStatus.FAILED
                job.matching_error = str(exc)
                db.commit()
                
                log_recruitment_event(
                    db=db,
                    event_type="MATCHING_FAILED",
                    job_id=job.id,
                    actor_id=actor_id,
                    metadata={"error": str(exc)}
                )
        except Exception as db_err:
            logger.critical(f"Failed to record matching failure status in DB: {str(db_err)}")
            
    finally:
        db.close()
