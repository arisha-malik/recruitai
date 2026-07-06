from typing import List, Optional
from pydantic import BaseModel

class SummaryStatsOut(BaseModel):
    total_candidates: int
    total_jobs: int
    total_applications: int
    total_matches: int
    shortlist_rate: float  # Percentage of shortlisted applications

class FunnelStageCount(BaseModel):
    stage: str
    count: int
    percentage_of_total: float

class PipelineFunnelOut(BaseModel):
    job_id: Optional[str] = None
    stages: List[FunnelStageCount]

class TimeToHireGroup(BaseModel):
    group_name: str
    average_days: float
    completed_hires_count: int

class TimeToHireOut(BaseModel):
    overall: TimeToHireGroup
    by_department: List[TimeToHireGroup]
    by_job: List[TimeToHireGroup]

class ScoreBucket(BaseModel):
    bucket: str
    count: int

class RecommendationCount(BaseModel):
    recommendation: str
    count: int

class ShortlistStatsOut(BaseModel):
    job_id: Optional[str] = None
    total_evaluated: int
    average_match_score: float
    score_distribution: List[ScoreBucket]
    recommendation_counts: List[RecommendationCount]

# New Phase 5 Schemas
from datetime import datetime
from typing import Dict

class RecentActivityEvent(BaseModel):
    id: str
    event_type: str
    candidate_id: Optional[str] = None
    job_id: Optional[str] = None
    actor_id: Optional[str] = None
    metadata_json: Optional[Dict] = None
    created_at: datetime

    class Config:
        from_attributes = True

class DashboardSummaryOut(BaseModel):
    total_candidates: int
    total_jobs: int
    open_jobs: int
    total_applications: int
    shortlisted_candidates: int
    interviewing_candidates: int
    offered_candidates: int
    rejected_candidates: int
    resumes_uploaded: int
    resumes_parsed: int
    resumes_failed: int
    matches_generated: int
    average_match_score: float
    recent_activity: List[RecentActivityEvent]

class CandidatePipelineOut(BaseModel):
    status_counts: Dict[str, int]
    status_percentages: Dict[str, float]

class ResumeParsingAnalyticsOut(BaseModel):
    total_resumes: int
    uploaded: int
    parsing: int
    parsed: int
    failed: int
    parse_success_rate: float
    parse_failure_rate: float
    average_parse_time_seconds: Optional[float] = None

class MatchingAnalyticsOut(BaseModel):
    total_match_results: int
    average_match_percentage: float
    strong_fit_count: int
    good_fit_count: int
    possible_fit_count: int
    weak_fit_count: int
    recommendation_breakdown: Dict[str, int]

class JobCandidateMatch(BaseModel):
    candidate_id: str
    first_name: str
    last_name: str
    email: str
    match_percentage: float
    final_recommendation: str

class JobAnalyticsOut(BaseModel):
    job_id: str
    job_title: str
    total_applications: int
    total_matches: int
    average_match_score: float
    top_matched_candidates: List[JobCandidateMatch]
    pipeline_breakdown: Dict[str, int]
    shortlisted_count: int
    interviewing_count: int
    offered_count: int
    rejected_count: int

class RecruitmentEventOut(BaseModel):
    id: str
    event_type: str
    candidate_id: Optional[str] = None
    job_id: Optional[str] = None
    actor_id: Optional[str] = None
    metadata_json: Optional[Dict] = None
    created_at: datetime

    class Config:
        from_attributes = True

class RecruitmentEventsTimelineOut(BaseModel):
    events: List[RecruitmentEventOut]
    total: int

class SourceEffectivenessGroup(BaseModel):
    source: str
    candidate_count: int
    shortlisted_count: int
    interviewing_count: int
    offered_count: int
    conversion_rate: float

class SourceEffectivenessOut(BaseModel):
    sources: List[SourceEffectivenessGroup]

class TimeToHireAnalyticsOut(BaseModel):
    average_time_to_offer_days: Optional[float] = None
    average_time_to_reject_days: Optional[float] = None
    average_time_in_pipeline_days: Optional[float] = None

class RecruiterActivity(BaseModel):
    user_id: str
    name: str
    resumes_uploaded: int
    jobs_created: int
    matches_run: int
    candidates_shortlisted: int
    interview_questions_generated: int
    jds_generated: int

class RecruiterActivityOut(BaseModel):
    recruiters: List[RecruiterActivity]
