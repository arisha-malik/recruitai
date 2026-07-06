from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User, UserRole
from app.schemas.analytics import (
    SummaryStatsOut,
    PipelineFunnelOut,
    TimeToHireOut,
    ShortlistStatsOut,
    DashboardSummaryOut,
    CandidatePipelineOut,
    ResumeParsingAnalyticsOut,
    MatchingAnalyticsOut,
    JobAnalyticsOut,
    RecruitmentEventsTimelineOut,
    SourceEffectivenessOut,
    TimeToHireAnalyticsOut,
    RecruiterActivityOut
)
from app.services.analytics_service import AnalyticsService
from app.dependencies import get_current_user, RoleChecker

router = APIRouter(prefix="/analytics", tags=["Dashboard & Analytics"])

# ==========================================
# Legacy Compatibility Endpoints
# ==========================================

@router.get(
    "/dashboard/summary",
    response_model=SummaryStatsOut,
    dependencies=[Depends(RoleChecker([UserRole.ADMIN, UserRole.RECRUITER, UserRole.HIRING_MANAGER]))]
)
def get_dashboard_summary_legacy(db: Session = Depends(get_db)):
    """
    Get high-level summary recruitment metrics (totals and shortlist rate) - Legacy.
    """
    return AnalyticsService.get_summary_stats(db)

@router.get(
    "/dashboard/funnel",
    response_model=PipelineFunnelOut,
    dependencies=[Depends(RoleChecker([UserRole.ADMIN, UserRole.RECRUITER, UserRole.HIRING_MANAGER]))]
)
def get_recruitment_funnel_legacy(
    job_id: Optional[str] = Query(None, description="Filter funnel by Job ID"),
    db: Session = Depends(get_db)
):
    """
    Get aggregated funnel stage counts and conversions, optionally filtered by Job ID - Legacy.
    """
    return AnalyticsService.get_pipeline_funnel(db, job_id)

@router.get(
    "/dashboard/time-to-hire",
    response_model=TimeToHireOut,
    dependencies=[Depends(RoleChecker([UserRole.ADMIN, UserRole.RECRUITER, UserRole.HIRING_MANAGER]))]
)
def get_time_to_hire_stats_legacy(db: Session = Depends(get_db)):
    """
    Get average days elapsed between application submission and OFFERED status - Legacy.
    """
    return AnalyticsService.get_time_to_hire(db)

@router.get(
    "/dashboard/shortlisting",
    response_model=ShortlistStatsOut,
    dependencies=[Depends(RoleChecker([UserRole.ADMIN, UserRole.RECRUITER, UserRole.HIRING_MANAGER]))]
)
def get_shortlisting_statistics_legacy(
    job_id: Optional[str] = Query(None, description="Filter statistics by Job ID"),
    db: Session = Depends(get_db)
):
    """
    Get shortlisting statistics - Legacy.
    """
    return AnalyticsService.get_shortlisting_stats(db, job_id)


# ==========================================
# Phase 5 Recruitment Analytics Endpoints
# ==========================================

@router.get(
    "/dashboard-summary",
    response_model=DashboardSummaryOut,
    dependencies=[Depends(RoleChecker([UserRole.ADMIN, UserRole.RECRUITER, UserRole.HIRING_MANAGER]))]
)
def get_dashboard_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns a unified summary of candidates, jobs, applications, parsing status, and recent activity.
    Recruiter sees filtered metrics relative to their own actions and created jobs.
    """
    return AnalyticsService.get_dashboard_summary(db, current_user)

@router.get(
    "/candidate-pipeline",
    response_model=CandidatePipelineOut,
    dependencies=[Depends(RoleChecker([UserRole.ADMIN, UserRole.RECRUITER, UserRole.HIRING_MANAGER]))]
)
def get_candidate_pipeline(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns application stage counts and conversion percentages.
    Recruiter is limited to applications of their own created jobs.
    """
    return AnalyticsService.get_candidate_pipeline(db, current_user)

@router.get(
    "/resume-parsing",
    response_model=ResumeParsingAnalyticsOut,
    dependencies=[Depends(RoleChecker([UserRole.ADMIN, UserRole.RECRUITER, UserRole.HIRING_MANAGER]))]
)
def get_resume_parsing(db: Session = Depends(get_db)):
    """
    Returns parsing statistics including upload totals, parsed/failed statuses, and success/failure rates.
    """
    return AnalyticsService.get_resume_parsing_analytics(db)

@router.get(
    "/matching",
    response_model=MatchingAnalyticsOut,
    dependencies=[Depends(RoleChecker([UserRole.ADMIN, UserRole.RECRUITER, UserRole.HIRING_MANAGER]))]
)
def get_matching(db: Session = Depends(get_db)):
    """
    Returns AI candidate matching statistics: fit band counts and recommendation breakdowns.
    """
    return AnalyticsService.get_matching_analytics(db)

@router.get(
    "/jobs/{job_id}",
    response_model=JobAnalyticsOut,
    dependencies=[Depends(RoleChecker([UserRole.ADMIN, UserRole.RECRUITER, UserRole.HIRING_MANAGER]))]
)
def get_job_analytics(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns analytics details for a specific Job ID including pipeline counts and top 5 matched candidates.
    Recruiter must be the owner of the job.
    """
    return AnalyticsService.get_job_analytics(db, job_id, current_user)

@router.get(
    "/events",
    response_model=RecruitmentEventsTimelineOut,
    dependencies=[Depends(RoleChecker([UserRole.ADMIN, UserRole.RECRUITER, UserRole.HIRING_MANAGER]))]
)
def get_events(
    event_type: Optional[str] = Query(None),
    candidate_id: Optional[str] = Query(None),
    job_id: Optional[str] = Query(None),
    actor_id: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Returns a timeline list of recruitment events, filterable by type, candidate, job, actor, and date ranges.
    """
    return AnalyticsService.get_recruitment_events(
        db=db,
        event_type=event_type,
        candidate_id=candidate_id,
        job_id=job_id,
        actor_id=actor_id,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset
    )

@router.get(
    "/source-effectiveness",
    response_model=SourceEffectivenessOut,
    dependencies=[Depends(RoleChecker([UserRole.ADMIN, UserRole.RECRUITER, UserRole.HIRING_MANAGER]))]
)
def get_source_effectiveness(db: Session = Depends(get_db)):
    """
    Returns conversion and shortlisting metrics grouped by candidate source.
    """
    return AnalyticsService.get_source_effectiveness(db)

@router.get(
    "/time-to-hire",
    response_model=TimeToHireAnalyticsOut,
    dependencies=[Depends(RoleChecker([UserRole.ADMIN, UserRole.RECRUITER, UserRole.HIRING_MANAGER]))]
)
def get_time_to_hire(db: Session = Depends(get_db)):
    """
    Returns average pipeline duration and offer/reject transition times.
    """
    return AnalyticsService.get_time_to_hire_analytics(db)

@router.get(
    "/recruiter-activity",
    response_model=RecruiterActivityOut,
    dependencies=[Depends(RoleChecker([UserRole.ADMIN, UserRole.RECRUITER]))]
)
def get_recruiter_activity(db: Session = Depends(get_db)):
    """
    Returns activity counts (resumes uploaded, jobs created, matches run, shortlists) per recruiter.
    """
    return AnalyticsService.get_recruiter_activity(db)
