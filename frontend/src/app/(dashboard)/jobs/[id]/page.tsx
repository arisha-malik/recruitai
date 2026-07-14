'use client';

import React, { useEffect, useState, use } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import { DOMAIN_CATEGORIES } from '@/lib/constants';
import { Card } from '@/components/ui/Card';
import { LoadingState } from '@/components/ui/LoadingState';
import { ErrorState } from '@/components/ui/ErrorState';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { MatchScoreBadge } from '@/components/ui/MatchScoreBadge';
import { 
  Briefcase, 
  MapPin, 
  Building, 
  Tag, 
  Play, 
  ChevronDown, 
  ChevronUp, 
  X,
  ListFilter,
  ArrowLeft,
  Edit2,
  Clock
} from 'lucide-react';

interface JobDetails {
  id: string;
  title: string;
  department: string;
  domain: string;
  location: string;
  employment_type: string;
  experience_level: string;
  description: string;
  required_skills?: string[];
  status: string;
  created_at: string;
}

interface MatchResult {
  candidate_id: string;
  candidate_name: string;
  match_percentage: number;
  skill_match_analysis: string;
  matched_skills: string[];
  missing_skills: string[];
  strengths: string[];
  concerns: string[];
  final_recommendation: string;
  summary?: string;
  application_id?: string;
  experience_delta?: string;
  location_fit?: string;
  notice_period_fit?: string;
}

interface Application {
  id: string;
  status: string;
  applied_at: string;
  candidate?: {
    id: string;
    first_name: string;
    last_name: string;
    email: string;
  };
}

export default function JobDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const jobId = resolvedParams.id;
  const [job, setJob] = useState<JobDetails | null>(null);
  const [matches, setMatches] = useState<MatchResult[]>([]);
  const [applications, setApplications] = useState<Application[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Match polling / triggering state
  const [matchingStatus, setMatchingStatus] = useState<'IDLE' | 'RUNNING' | 'SUCCESS' | 'FAILED'>('IDLE');
  const [matchingError, setMatchingError] = useState<string | null>(null);

  // Expanded candidates list tracking
  const [expandedCandidates, setExpandedCandidates] = useState<Record<string, boolean>>({});

  // Edit Job State
  const [isEditing, setIsEditing] = useState(false);
  const [editForm, setEditForm] = useState<Partial<JobDetails>>({});
  const [editSkillsStr, setEditSkillsStr] = useState('');
  const [editLoading, setEditLoading] = useState(false);
  const [editError, setEditError] = useState<string | null>(null);

  const openEditModal = () => {
    if (job) {
      setEditForm({
        title: job.title,
        department: job.department || '',
        domain: job.domain || '',
        location: job.location || '',
        employment_type: job.employment_type || 'FULL_TIME',
        experience_level: job.experience_level || 'MID',
        description: job.description || '',
      });
      setEditSkillsStr((job.required_skills || []).join(', '));
      setIsEditing(true);
    }
  };

  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setEditLoading(true);
    setEditError(null);
    try {
      const payload = {
        ...editForm,
        required_skills: editSkillsStr.split(',').map(s => s.trim()).filter(Boolean)
      };
      const res = await api.patch(`/jobs/${jobId}`, payload);
      setJob(res.data);
      setIsEditing(false);
    } catch (err: any) {
      console.error(err);
      setEditError('Failed to update job details.');
    } finally {
      setEditLoading(false);
    }
  };

  const startPolling = () => {
    let attempts = 0;
    const interval = setInterval(async () => {
      attempts++;
      try {
        const res = await api.get(`/matching/jobs/${jobId}/status`);
        if (res.data.status === 'SUCCESS' || res.data.status === 'COMPLETED') {
          setMatchingStatus('SUCCESS');
          clearInterval(interval);
          // Re-fetch match scores
          const matchRes = await api.get(`/matching/jobs/${jobId}/results`);
          setMatches(matchRes.data.results || []);
        } else if (res.data.status === 'FAILED') {
          setMatchingStatus('FAILED');
          setMatchingError(res.data.error_message || 'Failed to run matching pipeline. Make sure candidates have parsed resumes in the database.');
          clearInterval(interval);
        }
      } catch (e: any) {
        console.error(e);
        setMatchingStatus('FAILED');
        setMatchingError('Failed to fetch job status. The backend server might be down or unreachable.');
        clearInterval(interval);
      }

      if (attempts > 300) {
        setMatchingStatus('FAILED');
        clearInterval(interval);
      }
    }, 3000);
  };

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      // 1. Fetch Job Description details
      const jobRes = await api.get(`/jobs/${jobId}`);
      setJob(jobRes.data);

      // 2. Fetch Match Results
      try {
        const matchRes = await api.get(`/matching/jobs/${jobId}/results`);
        setMatches(matchRes.data.results || []);
      } catch (e) {
        console.warn('Match results empty or not run yet:', e);
        setMatches([]);
      }

      // Check matching status
      if (jobRes.data.matching_status === 'COMPLETED') {
        setMatchingStatus('SUCCESS');
      } else if (jobRes.data.matching_status === 'FAILED') {
        setMatchingStatus('FAILED');
        setMatchingError(jobRes.data.matching_error || 'Failed to run matching pipeline. Make sure candidates have parsed resumes in the database.');
      } else if (jobRes.data.matching_status === 'MATCHING') {
        setMatchingStatus('RUNNING');
        startPolling();
      }

      // 3. Fetch Applications submitted for this job
      const appRes = await api.get('/applications/', {
        params: { job_id: jobId }
      });
      setApplications(appRes.data);
    } catch (err: any) {
      console.error(err);
      setError('Failed to fetch job details and candidate matches.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [jobId]);

  const [decisionLoading, setDecisionLoading] = useState<string | null>(null);

  const handleDecision = async (applicationId: string | undefined, decision: 'SHORTLIST' | 'REJECT' | 'MAYBE') => {
    if (!applicationId) {
      alert("This match doesn't have an associated application yet.");
      return;
    }
    setDecisionLoading(applicationId);
    try {
      await api.post(`/applications/${applicationId}/decision`, { decision });
      fetchData(); // Refresh to hide or update candidate
    } catch (err: any) {
      console.error(err);
      alert('Failed to save decision.');
    } finally {
      setDecisionLoading(null);
    }
  };

  const toggleCandidateExpand = (candidateId: string) => {
    setExpandedCandidates((prev) => ({
      ...prev,
      [candidateId]: !prev[candidateId]
    }));
  };

  const handleRunMatching = async () => {
    setMatchingStatus('RUNNING');
    try {
      await api.post(`/matching/jobs/${jobId}/run`);
      
      // Poll matching status
      startPolling();
    } catch (err: any) {
      console.error(err);
      setMatchingStatus('FAILED');
      if (err.response?.data?.detail) {
        setMatchingError(err.response.data.detail);
      } else {
        setMatchingError('Failed to trigger matching pipeline. The backend may have encountered an error.');
      }
    }
  };

  const handleUpdateApplicationStatus = async (appId: string, nextStatus: string) => {
    try {
      await api.patch(`/applications/${appId}/status`, { status: nextStatus });
      // Re-fetch applications to reflect pipeline status change
      const appRes = await api.get('/applications/', {
        params: { job_id: jobId }
      });
      setApplications(appRes.data);
    } catch (err) {
      console.error('Failed to update application status:', err);
    }
  };

  const handleUpdateJobStatus = async (newStatus: string) => {
    try {
      const res = await api.patch(`/jobs/${jobId}`, { status: newStatus });
      setJob(res.data);
    } catch (err: any) {
      console.error('Failed to update job status:', err);
      alert('Failed to update job status. ' + (err.response?.data?.detail || ''));
    }
  };

  if (loading) {
    return <LoadingState type="page" message="Loading job details..." />;
  }

  if (error || !job) {
    return <ErrorState message={error || 'Job post not found'} onRetry={fetchData} />;
  }

  return (
    <div className="space-y-8">
      {/* Back link */}
      <div>
        <Link
          href="/jobs"
          className="inline-flex items-center gap-2 text-sm font-semibold text-slate-400 hover:text-slate-200 transition-colors"
        >
          <ArrowLeft size={16} />
          Back to Jobs List
        </Link>
      </div>

      {/* Title block */}
      <Card className="bg-gradient-to-br from-[#161e31] to-[#121927]">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
          <div className="space-y-2">
            <div className="flex items-center gap-3">
              <h1 className="text-3xl font-extrabold text-slate-100">{job.title}</h1>
              <button
                onClick={openEditModal}
                className="p-1.5 text-slate-500 hover:text-indigo-400 hover:bg-indigo-500/10 rounded transition-colors"
                title="Edit Job"
              >
                <Edit2 size={18} />
              </button>
            </div>
            <div className="flex flex-wrap items-center gap-4 text-sm text-slate-400">
              <span className="flex items-center gap-1.5 font-medium">
                <Building size={16} className="text-slate-500" />
                {job.department}
              </span>
              <span className="bg-indigo-500/10 text-indigo-400 px-2 py-0.5 rounded text-xs font-bold uppercase tracking-wider">
                {job.domain}
              </span>
              <span className="flex items-center gap-1.5 font-medium">
                <MapPin size={16} className="text-slate-500" />
                {job.location}
              </span>
              <span className="bg-[#f1f4f0] px-2.5 py-0.5 border border-border rounded text-xs font-bold text-indigo-400 uppercase">
                {job.employment_type.replace(/_/g, ' ')}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="relative">
              <select
                value={job.status}
                onChange={(e) => handleUpdateJobStatus(e.target.value)}
                className="bg-slate-800 border border-[#223049] rounded-lg py-2 px-3 text-sm text-slate-300 font-bold focus:outline-none focus:border-indigo-500 transition-colors cursor-pointer appearance-none pr-8"
              >
                <option value="DRAFT">DRAFT</option>
                <option value="OPEN">OPEN</option>
                <option value="CLOSED">CLOSED</option>
              </select>
              <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-slate-400">
                <svg className="fill-current h-4 w-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20">
                  <path d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z"/>
                </svg>
              </div>
            </div>
            
            <button
              onClick={handleRunMatching}
              disabled={matchingStatus === 'RUNNING' || job.status !== 'OPEN'}
              title={job.status !== 'OPEN' ? 'Candidate matching is only available for OPEN jobs' : ''}
              className={`inline-flex items-center gap-2 text-sm font-semibold px-4 py-2 rounded-lg shadow-lg transition-all active:scale-95 ${
                matchingStatus === 'RUNNING'
                  ? 'bg-amber-500/10 border border-amber-500/30 text-amber-400 animate-pulse'
                  : job.status !== 'OPEN'
                  ? 'bg-slate-700 text-slate-400 cursor-not-allowed'
                  : 'bg-indigo-500 hover:bg-indigo-650 text-white'
              }`}
            >
              <Play size={14} className={matchingStatus === 'RUNNING' ? 'animate-spin' : ''} />
              {matchingStatus === 'RUNNING' ? 'Running AI Engine...' : 'Run Candidate Matching'}
            </button>
          </div>
        </div>
      </Card>

      {/* Description and Required Skills */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card title="Job Description" className="lg:col-span-2 space-y-4">
          <p className="text-sm text-slate-700 leading-relaxed whitespace-pre-line">
            {job.description}
          </p>
        </Card>

        <Card title="Required Skills" className="lg:col-span-1">
          <div className="flex flex-wrap gap-2">
            {job.required_skills && job.required_skills.length > 0 ? (
              job.required_skills.map((skill, idx) => (
                <span
                  key={idx}
                  className="bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-xs font-semibold px-3 py-1.5 rounded-lg flex items-center gap-1.5"
                >
                  <Tag size={12} />
                  {skill}
                </span>
              ))
            ) : (
              <span className="text-slate-500 text-sm">No specific skills listed.</span>
            )}
          </div>
        </Card>
      </div>

      {/* Ranked Candidate Matches */}
      <div className="space-y-4">
        <h3 className="text-xl font-bold text-slate-900 flex items-center gap-2">
          Ranked Candidate Matches
          <span className="text-xs bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 px-2 py-0.5 rounded font-medium">
            AI Ranked
          </span>
        </h3>

        {matchingStatus === 'FAILED' && (
          <div className="p-4 bg-rose-500/10 border border-rose-500/20 text-rose-400 rounded-lg text-sm">
            {matchingError || 'Failed to run matching pipeline. Make sure candidates have parsed resumes in the database.'}
          </div>
        )}

        {matches.length === 0 ? (
          <Card className="text-center py-10 text-slate-500 text-sm">
            {matchingStatus === 'RUNNING'
              ? 'Evaluating candidate resumes using AI Matching Engine... Please wait.'
              : 'No matching results generated yet. Click "Run Candidate Matching" to evaluate candidate profiles.'}
          </Card>
        ) : (
          <div className="space-y-4">
            {matches.map((match) => {
              const app = applications.find((a: any) => a.id === match.application_id);
              const isExpanded = !!expandedCandidates[match.candidate_id];
              return (
                <Card key={match.candidate_id} className="p-5 border-border/80 hover:border-indigo-500/20">
                  <div
                    onClick={() => toggleCandidateExpand(match.candidate_id)}
                    className="flex flex-col md:flex-row md:items-center justify-between cursor-pointer gap-4"
                  >
                    <div className="flex items-center gap-4">
                      {/* Score Circle */}
                      <div className="relative w-14 h-14 flex items-center justify-center rounded-full bg-slate-900 border border-[#223049] shrink-0">
                        <span className="text-lg font-bold text-slate-100">{Math.round(match.match_percentage)}%</span>
                        <svg className="absolute inset-0 w-full h-full transform -rotate-90" viewBox="0 0 100 100">
                          <circle cx="50" cy="50" r="46" fill="transparent" stroke="#223049" strokeWidth="6" />
                          <circle
                            cx="50" cy="50" r="46" fill="transparent"
                            stroke={match.match_percentage >= 80 ? '#10b981' : match.match_percentage >= 60 ? '#f59e0b' : '#ef4444'}
                            strokeWidth="6"
                            strokeDasharray={`${(match.match_percentage / 100) * 289} 289`}
                            strokeLinecap="round"
                          />
                        </svg>
                      </div>

                      {/* Basic Info */}
                      <div>
                        <h4 className="text-base font-bold text-slate-900 flex items-center gap-2">
                          {match.candidate_name}
                          <span className={`text-xs px-2 py-0.5 rounded font-medium ${
                            match.final_recommendation === 'STRONG MATCH' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' :
                            match.final_recommendation === 'GOOD MATCH' ? 'bg-blue-500/10 text-blue-400 border border-blue-500/20' :
                            match.final_recommendation === 'POSSIBLE MATCH' ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' :
                            'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                          }`}>
                            {match.final_recommendation}
                          </span>
                        </h4>
                        <div className="flex flex-wrap gap-x-4 gap-y-1 text-sm text-slate-400 mt-1">
                          <span className="flex items-center gap-1.5"><Briefcase size={14} /> {match.experience_delta}</span>
                          <span className="flex items-center gap-1.5"><MapPin size={14} /> {match.location_fit}</span>
                          <span className="flex items-center gap-1.5"><Clock size={14} /> {match.notice_period_fit}</span>
                        </div>
                      </div>
                    </div>

                    <div className="flex flex-wrap items-center gap-2 md:gap-4 shrink-0">
                      {/* Action Buttons */}
                      <div className="flex gap-2 mr-2" onClick={(e) => e.stopPropagation()}>
                        <button
                          type="button"
                          disabled={decisionLoading === match.application_id || app?.status === 'SHORTLISTED'}
                          onClick={() => handleDecision(match.application_id, 'SHORTLIST')}
                          className={`flex items-center gap-1 px-3 py-1.5 border text-xs font-semibold rounded shadow-sm transition-colors ${
                            app?.status === 'SHORTLISTED'
                              ? 'bg-emerald-100 text-emerald-700 border-emerald-300 opacity-80 cursor-default'
                              : 'bg-emerald-50 text-emerald-600 hover:bg-emerald-100 border-emerald-200'
                          }`}
                        >
                          {app?.status === 'SHORTLISTED' ? '✅ Shortlisted' : '✅ Shortlist'}
                        </button>
                        <button
                          type="button"
                          disabled={decisionLoading === match.application_id || app?.status === 'REJECTED'}
                          onClick={() => handleDecision(match.application_id, 'REJECT')}
                          className={`flex items-center gap-1 px-3 py-1.5 border text-xs font-semibold rounded shadow-sm transition-colors ${
                            app?.status === 'REJECTED'
                              ? 'bg-rose-100 text-rose-700 border-rose-300 opacity-80 cursor-default'
                              : 'bg-rose-50 text-rose-600 hover:bg-rose-100 border-rose-200'
                          }`}
                        >
                          {app?.status === 'REJECTED' ? '❌ Rejected' : '❌ Reject'}
                        </button>
                      </div>
                      
                      <div className="text-slate-500">
                        {isExpanded ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
                      </div>
                    </div>
                  </div>

                  {/* Expanded AI Match Details */}
                  {isExpanded && (
                    <div className="mt-6 pt-6 border-t border-[#223049] space-y-6 animate-fadeIn">
                      {/* Summary */}
                      {match.summary && (
                        <div>
                          <h5 className="text-xs font-bold text-[#424844] uppercase tracking-wider mb-2">
                            Evaluation Summary
                          </h5>
                          <p className="text-sm text-slate-700 leading-relaxed bg-[#f1f4f0] p-4 rounded-xl border border-border/60">
                            {match.summary}
                          </p>
                        </div>
                      )}

                      {/* Skills match lists */}
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="bg-emerald-500/5 border border-emerald-500/15 rounded-xl p-4">
                          <h5 className="text-xs font-bold text-emerald-400 uppercase tracking-wider mb-3">
                            Matched Skills ({match.matched_skills.length})
                          </h5>
                          <div className="flex flex-wrap gap-1.5">
                            {match.matched_skills.length > 0 ? (
                              match.matched_skills.map((skill, idx) => (
                                <span
                                  key={idx}
                                  className="bg-emerald-500/10 text-emerald-400 text-xs px-2.5 py-1 rounded"
                                >
                                  {skill}
                                </span>
                              ))
                            ) : (
                              <span className="text-slate-500 text-xs">None listed</span>
                            )}
                          </div>
                        </div>

                        <div className="bg-rose-500/5 border border-rose-500/15 rounded-xl p-4">
                          <h5 className="text-xs font-bold text-rose-400 uppercase tracking-wider mb-3">
                            Missing Skills ({match.missing_skills.length})
                          </h5>
                          <div className="flex flex-wrap gap-1.5">
                            {match.missing_skills.length > 0 ? (
                              match.missing_skills.map((skill, idx) => (
                                <span
                                  key={idx}
                                  className="bg-rose-500/10 text-rose-400 text-xs px-2.5 py-1 rounded"
                                >
                                  {skill}
                                </span>
                              ))
                            ) : (
                              <span className="text-slate-500 text-xs">No critical gaps</span>
                            )}
                          </div>
                        </div>
                      </div>

                      {/* Strengths and Concerns */}
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <h5 className="text-xs font-bold text-[#424844] uppercase tracking-wider mb-2">
                            Key Strengths
                          </h5>
                          <ul className="list-disc pl-4.5 text-slate-300 text-sm space-y-1.5">
                            {match.strengths.map((str, idx) => (
                              <li key={idx} className="leading-relaxed">{str}</li>
                            ))}
                          </ul>
                        </div>
                        <div>
                          <h5 className="text-xs font-bold text-[#424844] uppercase tracking-wider mb-2">
                            Concerns / Risks
                          </h5>
                          <ul className="list-disc pl-4.5 text-slate-300 text-sm space-y-1.5">
                            {match.concerns.map((con, idx) => (
                              <li key={idx} className="leading-relaxed">{con}</li>
                            ))}
                          </ul>
                        </div>
                      </div>

                      {/* View candidate profile shortcut */}
                      <div className="flex justify-end pt-2">
                        <Link
                          href={`/candidates/${match.candidate_id}`}
                          className="text-xs font-bold text-indigo-400 hover:text-indigo-350 hover:underline"
                        >
                          View Full Candidate Profile →
                        </Link>
                      </div>
                    </div>
                  )}
                </Card>
              );
            })}
          </div>
        )}
      </div>

      {/* Applications Pipeline Status Updater */}
      <div className="space-y-4">
        <h3 className="text-xl font-bold text-slate-900 flex items-center gap-2">
          Hiring Pipeline Applications
          <span className="text-xs bg-blue-500/10 border border-blue-500/20 text-blue-400 px-2 py-0.5 rounded font-medium">
            Active
          </span>
        </h3>

        {applications.length === 0 ? (
          <Card className="text-center py-6 text-slate-500 text-sm">
            No candidates have submitted applications for this job opening yet.
          </Card>
        ) : (
          <div className="space-y-3">
            {applications.map((app) => (
              <Card key={app.id} className="p-4 bg-[#f1f4f0] border-border/80">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                  <div>
                    <h4 className="text-sm font-bold text-slate-900">
                      {app.candidate?.first_name} {app.candidate?.last_name}
                    </h4>
                    <p className="text-xs text-slate-400 mt-1">{app.candidate?.email}</p>
                  </div>

                  <div className="flex flex-wrap items-center gap-3">
                    <StatusBadge status={app.status} />

                    {/* Status actions dropdown */}
                    <div className="relative">
                      <select
                        value={app.status}
                        onChange={(e) => handleUpdateApplicationStatus(app.id, e.target.value)}
                        className="bg-slate-800 border border-[#223049] rounded-lg py-1 px-2.5 text-xs text-slate-300 font-bold focus:outline-none"
                      >
                        <option value="APPLIED">Applied</option>
                        <option value="SHORTLISTED">Shortlisted</option>
                        <option value="INTERVIEWING">Interviewing</option>
                        <option value="OFFERED">Offered</option>
                        <option value="REJECTED">Rejected</option>
                      </select>
                    </div>

                    <Link
                      href={`/candidates/${app.candidate?.id}`}
                      className="bg-[#f1f4f0] hover:bg-[#e6e9e4] text-xs font-semibold px-2.5 py-1.5 border border-border rounded-lg text-[#334155] transition-colors"
                    >
                      View Profile
                    </Link>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Edit Job Modal */}
      {isEditing && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <Card className="w-full max-w-xl shadow-2xl relative z-10 animate-scaleUp max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl font-bold text-slate-900">Edit Job Profile</h3>
              <button onClick={() => setIsEditing(false)} className="text-slate-400 hover:text-white">
                <X size={20} />
              </button>
            </div>

            {editError && (
              <div className="mb-4 p-3 bg-rose-500/10 border border-rose-500/20 text-rose-400 rounded-lg text-sm font-medium">
                {editError}
              </div>
            )}

            <form onSubmit={handleEditSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-[#424844] uppercase tracking-wider mb-1">
                  Job Title *
                </label>
                <input
                  type="text"
                  value={editForm.title || ''}
                  onChange={(e) => setEditForm({...editForm, title: e.target.value})}
                  className="w-full bg-white border border-[#e6e9e4] rounded-lg py-2 px-3 text-sm text-[#191c1a] focus:outline-none focus:border-[#476353] focus:ring-1 focus:ring-[#476353]"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-[#424844] uppercase tracking-wider mb-1">
                    Department
                  </label>
                  <input
                    type="text"
                    value={editForm.department || ''}
                    onChange={(e) => setEditForm({...editForm, department: e.target.value})}
                    className="w-full bg-white border border-[#e6e9e4] rounded-lg py-2 px-3 text-sm text-[#191c1a] focus:outline-none focus:border-[#476353] focus:ring-1 focus:ring-[#476353]"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-[#424844] uppercase tracking-wider mb-1">
                    Domain / Field
                  </label>
                  <select
                    value={editForm.domain || ''}
                    onChange={(e) => setEditForm({...editForm, domain: e.target.value})}
                    className="w-full bg-white border border-[#e6e9e4] rounded-lg py-2 px-3 text-sm text-[#191c1a] focus:outline-none focus:border-[#476353] focus:ring-1 focus:ring-[#476353]"
                  >
                    <option value="">Select Domain</option>
                    {DOMAIN_CATEGORIES.map(cat => (
                      <option key={cat} value={cat}>{cat.replace('_', ' ')}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-[#424844] uppercase tracking-wider mb-1">
                    Location
                  </label>
                  <select
                    value={editForm.location || ''}
                    onChange={(e) => setEditForm({...editForm, location: e.target.value})}
                    className="w-full bg-white border border-[#e6e9e4] rounded-lg py-2 px-3 text-sm text-[#424844] focus:outline-none focus:border-[#476353] focus:ring-1 focus:ring-[#476353]"
                  >
                    <option value="">Any / Open</option>
                    <option value="Delhi">Delhi</option>
                    <option value="Gurgaon">Gurgaon</option>
                    <option value="Manesar">Manesar</option>
                    <option value="Amravati">Amravati</option>
                    <option value="Remote">Remote</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-[#424844] uppercase tracking-wider mb-1">
                    Employment Type
                  </label>
                  <select
                    value={editForm.employment_type || ''}
                    onChange={(e) => setEditForm({...editForm, employment_type: e.target.value})}
                    className="w-full bg-white border border-[#e6e9e4] rounded-lg py-2 px-3 text-sm text-[#424844] focus:outline-none focus:border-[#476353] focus:ring-1 focus:ring-[#476353]"
                  >
                    <option value="FULL_TIME">Full Time</option>
                    <option value="PART_TIME">Part Time</option>
                    <option value="CONTRACT">Contract</option>
                    <option value="INTERNSHIP">Internship</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-[#424844] uppercase tracking-wider mb-1">
                    Experience Level
                  </label>
                  <select
                    value={editForm.experience_level || ''}
                    onChange={(e) => setEditForm({...editForm, experience_level: e.target.value})}
                    className="w-full bg-white border border-[#e6e9e4] rounded-lg py-2 px-3 text-sm text-[#424844] focus:outline-none focus:border-[#476353] focus:ring-1 focus:ring-[#476353]"
                  >
                    <option value="JUNIOR">Junior (Entry)</option>
                    <option value="MID">Mid (Associate)</option>
                    <option value="SENIOR">Senior (Lead)</option>
                    <option value="EXECUTIVE">Executive</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-[#424844] uppercase tracking-wider mb-1">
                  Required Skills (comma-separated)
                </label>
                <input
                  type="text"
                  value={editSkillsStr}
                  onChange={(e) => setEditSkillsStr(e.target.value)}
                  className="w-full bg-white border border-[#e6e9e4] rounded-lg py-2 px-3 text-sm text-[#191c1a] focus:outline-none focus:border-[#476353] focus:ring-1 focus:ring-[#476353]"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-[#424844] uppercase tracking-wider mb-1">
                  Job Description
                </label>
                <textarea
                  value={editForm.description || ''}
                  onChange={(e) => setEditForm({...editForm, description: e.target.value})}
                  rows={4}
                  className="w-full bg-white border border-[#e6e9e4] rounded-lg py-2 px-3 text-sm text-[#191c1a] focus:outline-none focus:border-[#476353] focus:ring-1 focus:ring-[#476353]"
                />
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t border-border">
                <button
                  type="button"
                  onClick={() => setIsEditing(false)}
                  className="px-4 py-2 text-sm font-semibold text-slate-400 hover:text-slate-200 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={editLoading}
                  className="bg-indigo-500 hover:bg-indigo-600 text-white text-sm font-semibold px-6 py-2 rounded-lg shadow-lg hover:shadow-indigo-500/20 transition-all active:scale-95 disabled:opacity-70 disabled:pointer-events-none"
                >
                  {editLoading ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            </form>
          </Card>
        </div>
      )}
    </div>
  );
}
