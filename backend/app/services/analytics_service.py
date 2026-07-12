from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.candidate import Candidate
from app.models.job import Job
from app.models.application import Application, ApplicationStatus, MatchResult

class AnalyticsService:
    @staticmethod
    def get_summary_stats(db: Session) -> Dict[str, Any]:
        """
        Aggregate overall stats: total candidates, jobs, applications, matches, and shortlist rate.
        """
        total_candidates = db.query(func.count(Candidate.id)).scalar() or 0
        total_jobs = db.query(func.count(Job.id)).scalar() or 0
        total_applications = db.query(func.count(Application.id)).scalar() or 0
        total_matches = db.query(func.count(MatchResult.id)).scalar() or 0
        
        shortlisted_apps = db.query(func.count(Application.id)).filter(
            Application.status == ApplicationStatus.SHORTLISTED
        ).scalar() or 0
        
        shortlist_rate = (shortlisted_apps / total_applications * 100.0) if total_applications > 0 else 0.0
        
        return {
            "total_candidates": total_candidates,
            "total_jobs": total_jobs,
            "total_applications": total_applications,
            "total_matches": total_matches,
            "shortlist_rate": round(shortlist_rate, 2)
        }

    @staticmethod
    def get_pipeline_funnel(db: Session, job_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Calculate candidate counts at each stage of the funnel.
        Funnel stage logic:
        - APPLIED: Everyone who has applied.
        - MATCHED: Status is MATCHED or further (SHORTLISTED, INTERVIEWING, OFFERED).
        - SHORTLISTED: Status is SHORTLISTED or further (INTERVIEWING, OFFERED).
        - INTERVIEWING: Status is INTERVIEWING or further (OFFERED).
        - OFFERED: Status is OFFERED.
        - REJECTED: Status is REJECTED.
        """
        query = db.query(Application)
        if job_id:
            query = query.filter(Application.job_id == job_id)
            
        apps = query.all()
        total_count = len(apps)
        
        # Initialize counts
        applied = total_count
        matched = 0
        shortlisted = 0
        interviewing = 0
        offered = 0
        rejected = 0
        
        for app in apps:
            status = app.status
            if status == ApplicationStatus.REJECTED:
                rejected += 1
            
            # Funnel progression logic
            if status in [
                ApplicationStatus.MATCHED,
                ApplicationStatus.SHORTLISTED,
                ApplicationStatus.INTERVIEWING,
                ApplicationStatus.OFFERED
            ]:
                matched += 1
            if status in [
                ApplicationStatus.SHORTLISTED,
                ApplicationStatus.INTERVIEWING,
                ApplicationStatus.OFFERED
            ]:
                shortlisted += 1
            if status in [
                ApplicationStatus.INTERVIEWING,
                ApplicationStatus.OFFERED
            ]:
                interviewing += 1
            if status == ApplicationStatus.OFFERED:
                offered += 1
                
        stages_data = [
            ("APPLIED", applied),
            ("MATCHED", matched),
            ("SHORTLISTED", shortlisted),
            ("INTERVIEWING", interviewing),
            ("OFFERED", offered),
            ("REJECTED", rejected)
        ]
        
        stages = []
        for stage_name, count in stages_data:
            pct = (count / total_count * 100.0) if total_count > 0 else 0.0
            stages.append({
                "stage": stage_name,
                "count": count,
                "percentage_of_total": round(pct, 2)
            })
            
        return {
            "job_id": job_id,
            "stages": stages
        }

    @staticmethod
    def get_time_to_hire(db: Session) -> Dict[str, Any]:
        """
        Computes average recruitment time from applied_at to OFFERED.
        Database-agnostic Python calculation to handle SQLite & Postgres differences.
        """
        # Fetch all offered applications
        offered_apps = db.query(Application).join(Job).filter(
            Application.status == ApplicationStatus.OFFERED
        ).all()
        
        if not offered_apps:
            empty_group = {"group_name": "Overall", "average_days": 0.0, "completed_hires_count": 0}
            return {
                "overall": empty_group,
                "by_department": [],
                "by_job": []
            }
            
        overall_deltas = []
        dept_deltas = {}
        job_deltas = {}
        
        for app in offered_apps:
            # Difference in days
            delta_days = (app.updated_at - app.applied_at).total_seconds() / 86400.0
            # Ensure it is at least 0
            delta_days = max(0.0, delta_days)
            
            overall_deltas.append(delta_days)
            
            # Department grouping
            dept = app.job.department
            if dept not in dept_deltas:
                dept_deltas[dept] = []
            dept_deltas[dept].append(delta_days)
            
            # Job grouping
            job_title = app.job.title
            if job_title not in job_deltas:
                job_deltas[job_title] = []
            job_deltas[job_title].append(delta_days)
            
        overall_avg = sum(overall_deltas) / len(overall_deltas)
        
        by_dept_list = []
        for dept, deltas in dept_deltas.items():
            by_dept_list.append({
                "group_name": dept,
                "average_days": round(sum(deltas) / len(deltas), 2),
                "completed_hires_count": len(deltas)
            })
            
        by_job_list = []
        for job, deltas in job_deltas.items():
            by_job_list.append({
                "group_name": job,
                "average_days": round(sum(deltas) / len(deltas), 2),
                "completed_hires_count": len(deltas)
            })
            
        return {
            "overall": {
                "group_name": "Overall",
                "average_days": round(overall_avg, 2),
                "completed_hires_count": len(overall_deltas)
            },
            "by_department": sorted(by_dept_list, key=lambda x: x["group_name"]),
            "by_job": sorted(by_job_list, key=lambda x: x["group_name"])
        }

    @staticmethod
    def get_shortlisting_stats(db: Session, job_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Aggregate candidate match percentage distribution and final recommendation counts.
        """
        query = db.query(MatchResult)
        if job_id:
            query = query.filter(MatchResult.job_id == job_id)
            
        matches = query.all()
        total_evaluated = len(matches)
        
        if total_evaluated == 0:
            return {
                "job_id": job_id,
                "total_evaluated": 0,
                "average_match_score": 0.0,
                "score_distribution": [
                    {"bucket": "0-20%", "count": 0},
                    {"bucket": "21-40%", "count": 0},
                    {"bucket": "41-60%", "count": 0},
                    {"bucket": "61-80%", "count": 0},
                    {"bucket": "81-100%", "count": 0}
                ],
                "recommendation_counts": [
                    {"recommendation": "SHORTLIST", "count": 0},
                    {"recommendation": "MAYBE", "count": 0},
                    {"recommendation": "REJECT", "count": 0}
                ]
            }
            
        total_score = 0.0
        buckets = {
            "0-20%": 0,
            "21-40%": 0,
            "41-60%": 0,
            "61-80%": 0,
            "81-100%": 0
        }
        recs = {
            "SHORTLIST": 0,
            "MAYBE": 0,
            "REJECT": 0
        }
        
        for m in matches:
            score = m.match_percentage
            total_score += score
            
            # Buckets logic
            if score <= 20.0:
                buckets["0-20%"] += 1
            elif score <= 40.0:
                buckets["21-40%"] += 1
            elif score <= 60.0:
                buckets["41-60%"] += 1
            elif score <= 80.0:
                buckets["61-80%"] += 1
            else:
                buckets["81-100%"] += 1
                
            # Recommendations logic
            r = m.final_recommendation.upper()
            if r in recs:
                recs[r] += 1
            else:
                recs["MAYBE"] += 1
                
        avg_score = total_score / total_evaluated
        
        distribution = [{"bucket": k, "count": v} for k, v in buckets.items()]
        recommendation_counts = [{"recommendation": k, "count": v} for k, v in recs.items()]
        
        return {
            "job_id": job_id,
            "total_evaluated": total_evaluated,
            "average_match_score": round(avg_score, 2),
            "score_distribution": distribution,
            "recommendation_counts": recommendation_counts
        }

    @staticmethod
    def get_dashboard_summary(db: Session, current_user: Any) -> Dict[str, Any]:
        from app.models.user import UserRole
        from app.models.candidate import Candidate, Resume, ParsingStatus
        from app.models.job import Job, JobStatus
        from app.models.application import Application, ApplicationStatus, MatchResult
        from app.models.audit import RecruitmentEvent
        from sqlalchemy import func

        is_recruiter = current_user.role == UserRole.RECRUITER

        # 1. Jobs queries
        jobs_query = db.query(Job)
        if is_recruiter:
            jobs_query = jobs_query.filter(Job.created_by_id == current_user.id)
        
        total_jobs = jobs_query.count()
        open_jobs = jobs_query.filter(Job.status == JobStatus.OPEN).count()

        # 2. Candidates query
        if is_recruiter:
            total_candidates = db.query(func.count(Candidate.id)).filter(
                Candidate.id.in_(
                    db.query(RecruitmentEvent.candidate_id).filter(
                        RecruitmentEvent.event_type == "CANDIDATE_CREATED",
                        RecruitmentEvent.actor_id == current_user.id
                    )
                )
            ).scalar() or 0
        else:
            total_candidates = db.query(func.count(Candidate.id)).scalar() or 0

        # 3. Applications queries
        apps_query = db.query(Application)
        if is_recruiter:
            apps_query = apps_query.join(Job).filter(Job.created_by_id == current_user.id)
        
        total_applications = apps_query.count()
        shortlisted_candidates = apps_query.filter(Application.status == ApplicationStatus.SHORTLISTED).count()
        interviewing_candidates = apps_query.filter(Application.status == ApplicationStatus.INTERVIEWING).count()
        offered_candidates = apps_query.filter(Application.status == ApplicationStatus.OFFERED).count()
        rejected_candidates = apps_query.filter(Application.status == ApplicationStatus.REJECTED).count()

        # 4. Resumes queries
        if is_recruiter:
            resumes_uploaded = db.query(RecruitmentEvent).filter(
                RecruitmentEvent.event_type == "RESUME_UPLOADED",
                RecruitmentEvent.actor_id == current_user.id
            ).count()
            resumes_parsed = db.query(RecruitmentEvent).filter(
                RecruitmentEvent.event_type == "RESUME_PARSED",
                RecruitmentEvent.actor_id == current_user.id
            ).count()
            resumes_failed = db.query(RecruitmentEvent).filter(
                RecruitmentEvent.event_type == "RESUME_PARSING_FAILED",
                RecruitmentEvent.actor_id == current_user.id
            ).count()
        else:
            resumes_uploaded = db.query(Resume).count()
            resumes_parsed = db.query(Resume).filter(Resume.parsing_status == ParsingStatus.PARSED).count()
            resumes_failed = db.query(Resume).filter(Resume.parsing_status == ParsingStatus.FAILED).count()

        # 5. Matching queries
        matches_query = db.query(MatchResult)
        if is_recruiter:
            matches_query = matches_query.join(Job).filter(Job.created_by_id == current_user.id)
        
        matches_generated = matches_query.count()
        average_match_score = matches_query.with_entities(func.avg(MatchResult.match_percentage)).scalar() or 0.0

        # 6. Recent activity queries
        activity_query = db.query(RecruitmentEvent)
        if is_recruiter:
            from sqlalchemy import or_
            activity_query = activity_query.outerjoin(Job, RecruitmentEvent.job_id == Job.id).filter(
                or_(
                    RecruitmentEvent.actor_id == current_user.id,
                    Job.created_by_id == current_user.id
                )
            )
        
        recent_activity = activity_query.order_by(RecruitmentEvent.created_at.desc()).limit(10).all()

        return {
            "total_candidates": total_candidates,
            "total_jobs": total_jobs,
            "open_jobs": open_jobs,
            "total_applications": total_applications,
            "shortlisted_candidates": shortlisted_candidates,
            "interviewing_candidates": interviewing_candidates,
            "offered_candidates": offered_candidates,
            "rejected_candidates": rejected_candidates,
            "resumes_uploaded": resumes_uploaded,
            "resumes_parsed": resumes_parsed,
            "resumes_failed": resumes_failed,
            "matches_generated": matches_generated,
            "average_match_score": round(average_match_score, 2),
            "recent_activity": recent_activity
        }

    @staticmethod
    def get_candidate_pipeline(db: Session, current_user: Any) -> Dict[str, Any]:
        from app.models.user import UserRole
        from app.models.job import Job
        from app.models.application import Application, ApplicationStatus
        from sqlalchemy import func

        query = db.query(Application.status, func.count(Application.id)).group_by(Application.status)
        if current_user.role == UserRole.RECRUITER:
            query = query.join(Job).filter(Job.created_by_id == current_user.id)
        
        results = query.all()
        counts = {status.value if hasattr(status, "value") else str(status): count for status, count in results}

        # Initialize all ApplicationStatus values with 0
        status_counts = {status.value: counts.get(status.value, 0) for status in ApplicationStatus}
        total = sum(status_counts.values())

        status_percentages = {}
        for status, count in status_counts.items():
            pct = (count / total * 100.0) if total > 0 else 0.0
            status_percentages[status] = round(pct, 2)

        return {
            "status_counts": status_counts,
            "status_percentages": status_percentages
        }

    @staticmethod
    def get_resume_parsing_analytics(db: Session) -> Dict[str, Any]:
        from app.models.candidate import Resume, ParsingStatus
        from sqlalchemy import func

        results = db.query(Resume.parsing_status, func.count(Resume.id)).group_by(Resume.parsing_status).all()
        counts = {status.value if hasattr(status, "value") else str(status): count for status, count in results}

        total_resumes = sum(counts.values())
        uploaded = counts.get(ParsingStatus.UPLOADED.value, 0)
        parsing = counts.get(ParsingStatus.PARSING.value, 0)
        parsed = counts.get(ParsingStatus.PARSED.value, 0)
        failed = counts.get(ParsingStatus.FAILED.value, 0)

        success_rate = (parsed / total_resumes * 100.0) if total_resumes > 0 else 0.0
        failure_rate = (failed / total_resumes * 100.0) if total_resumes > 0 else 0.0

        return {
            "total_resumes": total_resumes,
            "uploaded": uploaded,
            "parsing": parsing,
            "parsed": parsed,
            "failed": failed,
            "parse_success_rate": round(success_rate, 2),
            "parse_failure_rate": round(failure_rate, 2),
            "average_parse_time_seconds": None
        }

    @staticmethod
    def get_matching_analytics(db: Session) -> Dict[str, Any]:
        from app.models.application import MatchResult
        from sqlalchemy import func, case

        stats = db.query(
            func.count(MatchResult.id).label("total"),
            func.avg(MatchResult.match_percentage).label("avg_pct")
        ).first()

        total = stats.total or 0
        avg_pct = stats.avg_pct or 0.0

        bands = db.query(
            func.sum(case((MatchResult.match_percentage >= 85.0, 1), else_=0)).label("strong"),
            func.sum(case(((MatchResult.match_percentage >= 70.0) & (MatchResult.match_percentage < 85.0), 1), else_=0)).label("good"),
            func.sum(case(((MatchResult.match_percentage >= 50.0) & (MatchResult.match_percentage < 70.0), 1), else_=0)).label("possible"),
            func.sum(case((MatchResult.match_percentage < 50.0, 1), else_=0)).label("weak")
        ).first()

        strong_fit_count = bands.strong or 0
        good_fit_count = bands.good or 0
        possible_fit_count = bands.possible or 0
        weak_fit_count = bands.weak or 0

        recs = db.query(MatchResult.final_recommendation, func.count(MatchResult.id)).group_by(MatchResult.final_recommendation).all()
        rec_dict = {r[0].upper(): r[1] for r in recs}
        recommendation_breakdown = {
            "SHORTLIST": rec_dict.get("SHORTLIST", 0),
            "MAYBE": rec_dict.get("MAYBE", 0),
            "REJECT": rec_dict.get("REJECT", 0)
        }

        return {
            "total_match_results": total,
            "average_match_percentage": round(avg_pct, 2),
            "strong_fit_count": strong_fit_count,
            "good_fit_count": good_fit_count,
            "possible_fit_count": possible_fit_count,
            "weak_fit_count": weak_fit_count,
            "recommendation_breakdown": recommendation_breakdown
        }

    @staticmethod
    def get_job_analytics(db: Session, job_id: str, current_user: Any) -> Dict[str, Any]:
        from app.models.user import UserRole
        from app.models.job import Job
        from app.models.candidate import Candidate
        from app.models.application import Application, ApplicationStatus, MatchResult
        from sqlalchemy import func
        from fastapi import HTTPException, status

        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

        if current_user.role == UserRole.RECRUITER and job.created_by_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have access to this job's analytics")

        total_applications = db.query(Application).filter(Application.job_id == job_id).count()
        
        matches_query = db.query(MatchResult).filter(MatchResult.job_id == job_id)
        total_matches = matches_query.count()
        average_match_score = matches_query.with_entities(func.avg(MatchResult.match_percentage)).scalar() or 0.0

        top_candidates = db.query(
            Candidate.id.label("candidate_id"),
            Candidate.first_name,
            Candidate.last_name,
            Candidate.email,
            MatchResult.match_percentage,
            MatchResult.final_recommendation
        ).join(MatchResult, Candidate.id == MatchResult.candidate_id).filter(
            MatchResult.job_id == job_id
        ).order_by(MatchResult.match_percentage.desc()).limit(5).all()

        top_candidates_list = []
        for c in top_candidates:
            top_candidates_list.append({
                "candidate_id": c.candidate_id,
                "first_name": c.first_name,
                "last_name": c.last_name,
                "email": c.email,
                "match_percentage": c.match_percentage,
                "final_recommendation": c.final_recommendation
            })

        pipeline = db.query(Application.status, func.count(Application.id)).filter(
            Application.job_id == job_id
        ).group_by(Application.status).all()

        counts = {status.value if hasattr(status, "value") else str(status): count for status, count in pipeline}
        pipeline_breakdown = {status.value: counts.get(status.value, 0) for status in ApplicationStatus}

        shortlisted_count = pipeline_breakdown.get(ApplicationStatus.SHORTLISTED.value, 0)
        interviewing_count = pipeline_breakdown.get(ApplicationStatus.INTERVIEWING.value, 0)
        offered_count = pipeline_breakdown.get(ApplicationStatus.OFFERED.value, 0)
        rejected_count = pipeline_breakdown.get(ApplicationStatus.REJECTED.value, 0)

        return {
            "job_id": job_id,
            "job_title": job.title,
            "total_applications": total_applications,
            "total_matches": total_matches,
            "average_match_score": round(average_match_score, 2),
            "top_matched_candidates": top_candidates_list,
            "pipeline_breakdown": pipeline_breakdown,
            "shortlisted_count": shortlisted_count,
            "interviewing_count": interviewing_count,
            "offered_count": offered_count,
            "rejected_count": rejected_count
        }

    @staticmethod
    def get_recruitment_events(
        db: Session,
        event_type: Optional[str] = None,
        candidate_id: Optional[str] = None,
        job_id: Optional[str] = None,
        actor_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        from app.models.audit import RecruitmentEvent
        
        query = db.query(RecruitmentEvent)
        if event_type:
            query = query.filter(RecruitmentEvent.event_type == event_type)
        if candidate_id:
            query = query.filter(RecruitmentEvent.candidate_id == candidate_id)
        if job_id:
            query = query.filter(RecruitmentEvent.job_id == job_id)
        if actor_id:
            query = query.filter(RecruitmentEvent.actor_id == actor_id)
        if start_date:
            query = query.filter(RecruitmentEvent.created_at >= start_date)
        if end_date:
            query = query.filter(RecruitmentEvent.created_at <= end_date)

        total = query.count()
        events = query.order_by(RecruitmentEvent.created_at.desc()).offset(offset).limit(limit).all()

        return {
            "events": events,
            "total": total
        }

    @staticmethod
    def get_source_effectiveness(db: Session) -> Dict[str, Any]:
        from app.models.candidate import Candidate
        from app.models.application import Application, ApplicationStatus
        from sqlalchemy import func, case

        results = db.query(
            Candidate.source,
            func.count(Candidate.id).label("candidate_count"),
            func.sum(case((Application.status == ApplicationStatus.SHORTLISTED, 1), else_=0)).label("shortlisted_count"),
            func.sum(case((Application.status == ApplicationStatus.INTERVIEWING, 1), else_=0)).label("interviewing_count"),
            func.sum(case((Application.status == ApplicationStatus.OFFERED, 1), else_=0)).label("offered_count")
        ).outerjoin(Application, Candidate.id == Application.candidate_id).group_by(Candidate.source).all()

        sources = []
        for r in results:
            source_name = r.source or "DIRECT_UPLOAD"
            candidate_count = r.candidate_count or 0
            shortlisted_count = r.shortlisted_count or 0
            interviewing_count = r.interviewing_count or 0
            offered_count = r.offered_count or 0

            conversion_rate = (offered_count / candidate_count * 100.0) if candidate_count > 0 else 0.0

            sources.append({
                "source": source_name,
                "candidate_count": candidate_count,
                "shortlisted_count": shortlisted_count,
                "interviewing_count": interviewing_count,
                "offered_count": offered_count,
                "conversion_rate": round(conversion_rate, 2)
            })

        sources.sort(key=lambda x: x["conversion_rate"], reverse=True)

        return {
            "sources": sources
        }

    @staticmethod
    def get_time_to_hire_analytics(db: Session) -> Dict[str, Any]:
        from app.models.application import Application, ApplicationStatus

        apps = db.query(
            Application.applied_at,
            Application.shortlisted_at,
            Application.interviewing_at,
            Application.offered_at,
            Application.rejected_at,
            Application.updated_at,
            Application.status
        ).all()

        if not apps:
            return {
                "average_time_to_offer_days": None,
                "average_time_to_reject_days": None,
                "average_time_in_pipeline_days": None
            }

        offer_days = []
        reject_days = []
        pipeline_days = []

        for app in apps:
            if app.updated_at and app.applied_at:
                pipeline_days.append(max(0.0, (app.updated_at - app.applied_at).total_seconds() / 86400.0))

            if app.status == ApplicationStatus.OFFERED and app.offered_at and app.applied_at:
                offer_days.append(max(0.0, (app.offered_at - app.applied_at).total_seconds() / 86400.0))
            
            if app.status == ApplicationStatus.REJECTED and app.rejected_at and app.applied_at:
                reject_days.append(max(0.0, (app.rejected_at - app.applied_at).total_seconds() / 86400.0))

        avg_offer = sum(offer_days) / len(offer_days) if offer_days else None
        avg_reject = sum(reject_days) / len(reject_days) if reject_days else None
        avg_pipeline = sum(pipeline_days) / len(pipeline_days) if pipeline_days else None

        return {
            "average_time_to_offer_days": round(avg_offer, 2) if avg_offer is not None else None,
            "average_time_to_reject_days": round(avg_reject, 2) if avg_reject is not None else None,
            "average_time_in_pipeline_days": round(avg_pipeline, 2) if avg_pipeline is not None else None
        }

    @staticmethod
    def get_recruiter_activity(db: Session) -> Dict[str, Any]:
        from app.models.user import User, UserRole
        from app.models.audit import RecruitmentEvent

        recruiters = db.query(User).filter(User.role.in_([UserRole.RECRUITER, UserRole.ADMIN])).all()
        if not recruiters:
            return {"recruiters": []}

        recruiter_ids = [r.id for r in recruiters]

        events = db.query(RecruitmentEvent).filter(
            RecruitmentEvent.actor_id.in_(recruiter_ids)
        ).all()

        stats = {
            r.id: {
                "user_id": r.id,
                "name": f"{r.first_name} {r.last_name}".strip() or r.email,
                "resumes_uploaded": 0,
                "jobs_created": 0,
                "matches_run": 0,
                "candidates_shortlisted": 0,
                "interview_questions_generated": 0,
                "jds_generated": 0
            } for r in recruiters
        }

        for ev in events:
            actor_id = ev.actor_id
            if not actor_id or actor_id not in stats:
                continue
            
            event_type = ev.event_type
            metadata_json = ev.metadata_json
            if isinstance(metadata_json, str):
                import json
                try:
                    metadata_json = json.loads(metadata_json)
                except Exception:
                    metadata_json = {}

            s = stats[actor_id]
            if event_type == "RESUME_UPLOADED":
                s["resumes_uploaded"] += 1
            elif event_type == "JOB_CREATED":
                s["jobs_created"] += 1
            elif event_type == "MATCHING_STARTED":
                s["matches_run"] += 1
            elif event_type == "APPLICATION_STATUS_CHANGED":
                meta = metadata_json or {}
                if meta.get("new_status") == "SHORTLISTED":
                    s["candidates_shortlisted"] += 1
            elif event_type == "INTERVIEW_QUESTIONS_GENERATED":
                s["interview_questions_generated"] += 1
            elif event_type == "JD_GENERATED":
                s["jds_generated"] += 1

        return {
            "recruiters": list(stats.values())
        }
