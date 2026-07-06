"use client";

import React, { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { 
  Users, 
  BriefcaseBusiness, 
  CheckCircle2, 
  FileCheck2,
  Activity,
  Award,
  Sparkles,
  TrendingUp,
  Clock,
  ChevronRight,
  CalendarClock,
  XCircle
} from "lucide-react";
import { Card } from "@/components/ui/Card";
import Link from "next/link";

interface ActivityItem {
  id: string;
  event_type: string;
  created_at: string;
  candidate_id?: string;
  job_id?: string;
  actor_id?: string;
  metadata_json?: any;
}

interface DashboardStats {
  total_candidates: number;
  total_jobs: number;
  open_jobs: number;
  total_applications: number;
  shortlisted_candidates: number;
  interviewing_candidates: number;
  offered_candidates: number;
  rejected_candidates: number;
  resumes_uploaded: number;
  resumes_parsed: number;
  resumes_failed: number;
  matches_generated: number;
  average_match_score: number;
  recent_activity: ActivityItem[];
}

export default function DashboardPage() {
  const [data, setData] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDashboardData = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.get("/analytics/dashboard-summary");
      setData(response.data);
    } catch (err: any) {
      console.error(err);
      setError("Failed to fetch dashboard statistics. Please check your backend connection.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const formatEventName = (eventType: string) => {
    return eventType
      .replace(/_/g, " ")
      .toLowerCase()
      .replace(/\b\w/g, (c) => c.toUpperCase());
  };

  const getActivityDescription = (activity: ActivityItem) => {
    const meta = activity.metadata_json || {};
    switch (activity.event_type) {
      case "USER_LOGIN":
        return `User logged in: ${meta.email || 'System User'}`;
      case "CANDIDATE_CREATED":
        return `Candidate profile created for ${meta.name || meta.email || 'New Candidate'}.`;
      case "RESUME_UPLOADED":
        return `Resume uploaded: ${meta.file_name || 'Resume.pdf'}.`;
      case "RESUME_PARSED":
        return `Resume successfully parsed.`;
      case "RESUME_PARSING_FAILED":
        return `Failed to parse resume: ${meta.error || 'Parsing error'}.`;
      case "JOB_CREATED":
        return `New job requisition created: ${meta.job_title || 'Job Opening'}.`;
      case "MATCHING_STARTED":
        return `Matching analysis started.`;
      case "APPLICATION_STATUS_CHANGED":
        return `Status updated to ${meta.new_status}.`;
      case "CANDIDATE_SHORTLISTED":
        return `Candidate shortlisted for interview round.`;
      case "CANDIDATE_REJECTED":
        return `Candidate rejected.`;
      case "CANDIDATE_MARKED_MAYBE":
        return `Candidate marked as maybe.`;
      default:
        return `Event recorded in system.`;
    }
  };

  if (loading) {
    return (
      <div className="p-8 space-y-6">
        <h2 className="text-3xl font-black text-slate-900 tracking-tight flex items-center gap-3">
          Dashboard
        </h2>
        <div className="flex justify-center py-20">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="p-8">
        <div className="bg-rose-500/10 border border-rose-500/20 text-rose-500 p-4 rounded-xl text-sm font-semibold">
          {error || "No data available."}
        </div>
      </div>
    );
  }

  const statCards = [
    {
      title: "Total Candidates",
      value: data.total_candidates.toString(),
      icon: Users,
      color: "text-[#4F46E5]",
      bgColor: "bg-[#EEF2FF]"
    },
    {
      title: "Resumes Parsed",
      value: data.resumes_parsed.toString(),
      icon: FileCheck2,
      color: "text-[#2563EB]",
      bgColor: "bg-[#EFF6FF]"
    },
    {
      title: "Open Jobs",
      value: data.open_jobs.toString(),
      icon: BriefcaseBusiness,
      color: "text-[#059669]",
      bgColor: "bg-[#ECFDF5]"
    },
    {
      title: "Matches Generated",
      value: data.matches_generated.toString(),
      icon: Sparkles,
      color: "text-[#D97706]",
      bgColor: "bg-[#FFFBEB]"
    }
  ];

  const pipelineCards = [
    { label: "Shortlisted", count: data.shortlisted_candidates, color: "text-emerald-600" },
    { label: "Interviewing", count: data.interviewing_candidates, color: "text-blue-600" },
    { label: "Rejected", count: data.rejected_candidates, color: "text-rose-600" }
  ];

  const hasNoData = data.total_candidates === 0 && data.total_jobs === 0;

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h2 className="text-[28px] md:text-[32px] font-bold text-slate-900 leading-tight">
            Recruitment Overview
          </h2>
          <p className="text-base font-medium text-slate-500 mt-1">Real-time statistics across your entire talent pipeline.</p>
        </div>
      </div>

      {hasNoData ? (
        <Card className="text-center py-20 text-slate-500 shadow-sm border-slate-200">
          <Activity className="mx-auto mb-4 opacity-30 text-indigo-500" size={64} />
          <h3 className="text-xl font-bold text-slate-800 mb-2">Welcome to RecruitAI!</h3>
          <p className="text-sm max-w-md mx-auto mb-6">
            Your dashboard is currently empty. Start by uploading a resume or creating your first job requisition to see analytics flow in.
          </p>
          <div className="flex justify-center gap-4">
            <Link href="/resumes/upload" className="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-lg transition-colors">
              Upload Resume
            </Link>
            <Link href="/jobs" className="px-6 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-800 font-bold border border-slate-200 rounded-lg transition-colors">
              Create Job
            </Link>
          </div>
        </Card>
      ) : (
        <>
          {/* Top Level Stats */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 md:gap-7">
            {statCards.map((stat, idx) => (
              <Card key={idx} className="p-6 border border-slate-200 shadow-[0_8px_24px_rgba(15,23,42,0.06)] rounded-[20px] flex items-center gap-4 bg-white hover:border-slate-300 transition-colors">
                <div className={`w-14 h-14 rounded-2xl flex items-center justify-center shrink-0 ${stat.bgColor} ${stat.color}`}>
                  <stat.icon size={26} strokeWidth={2.2} />
                </div>
                <div>
                  <p className="text-[13px] font-semibold text-slate-500 uppercase tracking-wide mb-1">{stat.title}</p>
                  <p className="text-[28px] md:text-[32px] font-bold text-slate-900 leading-none">{stat.value}</p>
                </div>
              </Card>
            ))}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left Column: Pipeline & Matching Stats */}
            <div className="lg:col-span-2 space-y-6 md:space-y-7">
              
              {/* Pipeline Overview */}
              <Card className="p-6 md:p-8 border-slate-200 shadow-[0_8px_24px_rgba(15,23,42,0.06)] rounded-[20px] bg-white">
                <h3 className="text-lg font-bold text-slate-900 mb-6 flex items-center gap-2">
                  <TrendingUp className="text-slate-500" size={22} strokeWidth={2.2} />
                  Active Pipeline
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  {pipelineCards.map((pipe, idx) => (
                    <div key={idx} className="flex flex-col items-start bg-slate-50/50 rounded-2xl p-5 border border-slate-100">
                      <p className="text-[13px] font-semibold text-slate-500 uppercase tracking-wide mb-2 flex items-center gap-2">
                        {pipe.label === 'Shortlisted' && <CheckCircle2 size={16} className={pipe.color} />}
                        {pipe.label === 'Interviewing' && <CalendarClock size={16} className={pipe.color} />}
                        {pipe.label === 'Rejected' && <XCircle size={16} className={pipe.color} />}
                        {pipe.label}
                      </p>
                      <p className={`text-[28px] font-bold ${pipe.color} leading-none`}>{pipe.count}</p>
                    </div>
                  ))}
                </div>
              </Card>

              {/* AI Matching Performance */}
              <Card className="p-6 md:p-8 border-slate-200 shadow-[0_8px_24px_rgba(15,23,42,0.06)] rounded-[20px] bg-white">
                <h3 className="text-lg font-bold text-slate-900 mb-6 flex items-center gap-2">
                  <Award className="text-slate-500" size={22} strokeWidth={2.2} />
                  AI Matching Performance
                </h3>
                <div className="flex flex-col sm:flex-row items-center sm:items-start gap-6">
                  <div className="relative w-[110px] h-[110px] flex items-center justify-center rounded-full bg-slate-50 border border-slate-200 shrink-0 shadow-sm">
                    <span className="text-[28px] font-bold text-slate-900">{Math.round(data.average_match_score)}<span className="text-base text-slate-500">%</span></span>
                    <svg className="absolute inset-[-1px] w-[112px] h-[112px] transform -rotate-90" viewBox="0 0 100 100">
                      <circle cx="50" cy="50" r="48" fill="transparent" stroke="transparent" strokeWidth="4" />
                      <circle
                        cx="50" cy="50" r="48" fill="transparent"
                        stroke="#059669"
                        strokeWidth="4"
                        strokeDasharray={`${(data.average_match_score / 100) * 301.5} 301.5`}
                        strokeLinecap="round"
                        className="transition-all duration-1000 ease-out drop-shadow-sm"
                      />
                    </svg>
                  </div>
                  <div>
                    <h4 className="text-base font-bold text-slate-800">Average Match Quality</h4>
                    <p className="text-sm text-slate-500 mt-2 max-w-sm leading-relaxed font-medium">
                      This represents the average AI-calculated fit score across all candidate-to-job matches generated in the system. High scores indicate strong alignment between candidate skills and job requirements.
                    </p>
                  </div>
                </div>
              </Card>
            </div>

            {/* Right Column: Activity Feed */}
            <div className="lg:col-span-1">
              <Card className="p-6 md:p-8 border-slate-200 shadow-[0_8px_24px_rgba(15,23,42,0.06)] rounded-[20px] h-full flex flex-col bg-white">
                <div className="flex justify-between items-center mb-6">
                  <h3 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                    <Activity className="text-slate-500" size={22} strokeWidth={2.2} />
                    Recent Activity
                  </h3>
                </div>
                
                <div className="flex-1 overflow-y-auto pr-2 space-y-6">
                  {data.recent_activity && data.recent_activity.length > 0 ? (
                    data.recent_activity.map((activity) => (
                      <div key={activity.id} className="relative pl-6 border-l-2 border-slate-100 pb-4 last:pb-0">
                        <div className="absolute w-2.5 h-2.5 bg-slate-300 rounded-full -left-[6px] top-1.5 shadow-[0_0_0_4px_white]"></div>
                        <p className="text-[14px] font-semibold text-slate-800">
                          {formatEventName(activity.event_type)}
                        </p>
                        <p className="text-[13px] text-slate-500 mt-1 leading-relaxed font-medium">
                          {getActivityDescription(activity)}
                        </p>
                        <p className="text-[11px] font-semibold text-slate-500 mt-2 flex items-center gap-1 uppercase tracking-wider">
                          <Clock size={12} strokeWidth={2.5} />
                          {new Date(activity.created_at).toLocaleString()}
                        </p>
                      </div>
                    ))
                  ) : (
                    <div className="text-center py-10 text-slate-500 text-sm">
                      No recent activity found.
                    </div>
                  )}
                </div>
              </Card>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
