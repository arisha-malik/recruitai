"use client";

import React, { useState, useEffect } from "react";
import { api } from "@/lib/api";
import {
  Users,
  HelpCircle,
  Briefcase,
  ChevronDown,
  ChevronUp,
  MapPin,
  Clock,
  Sparkles
} from "lucide-react";
import { Card } from "@/components/ui/Card";
import Link from "next/link";

export default function InterviewRoundPage() {
  const [applications, setApplications] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedCandidate, setExpandedCandidate] = useState<string | null>(null);

  // Question generation states
  const [generatingFor, setGeneratingFor] = useState<string | null>(null);
  const [generatedQuestions, setGeneratedQuestions] = useState<any | null>(null);

  // Configuration form states
  const [configuringFor, setConfiguringFor] = useState<string | null>(null);
  const [roundType, setRoundType] = useState('technical');
  const [topicOrSkill, setTopicOrSkill] = useState('');
  const [difficulty, setDifficulty] = useState('intermediate');
  const [count, setCount] = useState(5);

  useEffect(() => {
    fetchInterviewingCandidates();
  }, []);

  const fetchInterviewingCandidates = async () => {
    setLoading(true);
    try {
      // Fetch applications with status INTERVIEWING
      const res = await api.get('/applications/', {
        params: { status: 'INTERVIEWING' }
      });
      setApplications(res.data);
    } catch (err: any) {
      console.error(err);
      setError('Failed to fetch interview candidates.');
    } finally {
      setLoading(false);
    }
  };

  const handleOpenConfig = (app: any) => {
    setConfiguringFor(app.id);
    setExpandedCandidate(app.id);
    setGeneratedQuestions(null);
    setRoundType(app.round_type?.toLowerCase() || 'technical');
    setTopicOrSkill('');
    setDifficulty('intermediate');
    setCount(5);
  };

  const generateQuestions = async (app: any) => {
    if (!topicOrSkill.trim()) {
      alert("Please enter a topic or skill.");
      return;
    }
    
    setGeneratingFor(app.id);
    setGeneratedQuestions(null);
    try {
      // Create request payload
      const payload = {
        round_id: app.id,
        candidate_id: app.candidate?.id,
        job_id: app.job?.id,
        round_type: roundType,
        topic_or_skill: topicOrSkill,
        difficulty: difficulty,
        count: count
      };

      const res = await api.post('/assistant/interview-questions', payload);
      setGeneratedQuestions({
        appId: app.id,
        data: res.data.data
      });
      setConfiguringFor(null); // Close config
    } catch (err: any) {
      console.error(err);
      alert('Failed to generate questions. ' + (err.response?.data?.detail || ''));
    } finally {
      setGeneratingFor(null);
    }
  };

  if (loading) {
    return (
      <div className="p-8 space-y-6">
        <h2 className="text-3xl font-black text-slate-900 tracking-tight flex items-center gap-3">
          <Users className="text-indigo-600" size={32} />
          Interview Round
        </h2>
        <div className="flex justify-center py-20">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 space-y-6 max-w-7xl mx-auto">
      <div className="flex justify-between items-center">
        <h2 className="text-3xl font-black text-slate-900 tracking-tight flex items-center gap-3">
          <Users className="text-indigo-600" size={32} />
          Interview Round
        </h2>
      </div>

      {error && (
        <div className="bg-rose-500/10 border border-rose-500/20 text-rose-500 p-4 rounded-xl text-sm font-semibold">
          {error}
        </div>
      )}

      {applications.length === 0 ? (
        <Card className="text-center py-16 text-slate-500">
          <HelpCircle className="mx-auto mb-4 opacity-50" size={48} />
          <h3 className="text-lg font-bold text-slate-700 mb-2">No Candidates Interviewing</h3>
          <p className="text-sm">There are no candidates currently in the interview round.</p>
        </Card>
      ) : (
        <div className="grid gap-6">
          {applications.map((app) => {
            const isExpanded = expandedCandidate === app.id;
            const hasQuestions = generatedQuestions?.appId === app.id;

            return (
              <Card key={app.id} className="p-6 border-border/80 shadow-sm hover:shadow-md transition-shadow">
                <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
                  <div className="space-y-3 flex-1">
                    <div>
                      <h3 className="text-xl font-bold text-slate-900 hover:text-indigo-600 transition-colors">
                        <Link href={`/candidates/${app.candidate?.id}`}>
                          {app.candidate?.first_name} {app.candidate?.last_name}
                        </Link>
                      </h3>
                      <p className="text-indigo-600 font-semibold text-sm flex items-center gap-2 mt-1">
                        <Briefcase size={14} />
                        Applying for: {app.job?.title}
                      </p>
                    </div>

                    <div className="flex flex-wrap gap-4 text-sm text-slate-500">
                      <span className="flex items-center gap-1.5 bg-slate-100 px-2 py-1 rounded-md">
                        <MapPin size={14} />
                        {app.job?.location || 'Unknown'}
                      </span>
                      <span className="flex items-center gap-1.5 bg-slate-100 px-2 py-1 rounded-md">
                        <Clock size={14} />
                        {app.job?.department || 'General'}
                      </span>
                    </div>
                  </div>

                  <div className="flex flex-col sm:flex-row items-center gap-3 shrink-0">
                    <button
                      onClick={() => handleOpenConfig(app)}
                      className="w-full sm:w-auto px-4 py-2 bg-gradient-to-r from-indigo-600 to-purple-600 text-white text-sm font-bold rounded-lg hover:from-indigo-700 hover:to-purple-700 transition-all flex items-center justify-center gap-2 shadow-md shadow-indigo-500/20"
                    >
                      <Sparkles size={16} />
                      Generate Questions
                    </button>

                    <button
                      onClick={() => setExpandedCandidate(isExpanded ? null : app.id)}
                      className="p-2 text-slate-500 hover:text-slate-700 bg-slate-50 hover:bg-slate-100 rounded-lg transition-colors border border-slate-200"
                    >
                      {isExpanded ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
                    </button>
                  </div>
                </div>

                {isExpanded && configuringFor === app.id && !hasQuestions && (
                  <div className="mt-8 pt-6 border-t border-slate-100 animate-fadeIn">
                    <h4 className="text-lg font-bold text-slate-800 mb-4">Configure Questions</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                      <div>
                        <label className="block text-sm font-medium text-slate-700 mb-1">Round Type</label>
                        <select className="w-full p-2 border border-slate-300 rounded-md" value={roundType} onChange={e => setRoundType(e.target.value)}>
                          <option value="technical">Technical</option>
                          <option value="hr">HR</option>
                          <option value="managerial">Managerial</option>
                          <option value="assessment">Assessment</option>
                        </select>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-slate-700 mb-1">Topic / Skill</label>
                        <input type="text" className="w-full p-2 border border-slate-300 rounded-md" placeholder="e.g. Python, Leadership" value={topicOrSkill} onChange={e => setTopicOrSkill(e.target.value)} />
                        <p className="text-xs text-slate-500 mt-1">
                          {roundType === 'technical' && 'Suggestions: Python, Java, DevOps, AWS'}
                          {roundType === 'hr' && 'Suggestions: Communication, Team Collaboration'}
                          {roundType === 'managerial' && 'Suggestions: Leadership, Decision Making'}
                          {roundType === 'assessment' && 'Suggestions: Coding Task, System Design, Debugging'}
                        </p>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-slate-700 mb-1">Difficulty</label>
                        <select className="w-full p-2 border border-slate-300 rounded-md" value={difficulty} onChange={e => setDifficulty(e.target.value)}>
                          <option value="beginner">Beginner</option>
                          <option value="intermediate">Intermediate</option>
                          <option value="advanced">Advanced</option>
                        </select>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-slate-700 mb-1">Number of Questions</label>
                        <select className="w-full p-2 border border-slate-300 rounded-md" value={count} onChange={e => setCount(Number(e.target.value))}>
                          <option value={5}>5</option>
                          <option value={10}>10</option>
                          <option value={15}>15</option>
                        </select>
                      </div>
                    </div>
                    <button
                      onClick={() => generateQuestions(app)}
                      disabled={generatingFor === app.id}
                      className="px-6 py-2 bg-indigo-600 text-white text-sm font-bold rounded-lg hover:bg-indigo-700 disabled:opacity-50 transition-all flex items-center justify-center gap-2"
                    >
                      {generatingFor === app.id ? (
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                      ) : (
                        <Sparkles size={16} />
                      )}
                      Generate Now
                    </button>
                  </div>
                )}

                {isExpanded && hasQuestions && (
                  <div className="mt-8 pt-6 border-t border-slate-100 animate-fadeIn">
                    <div className="flex flex-wrap items-center gap-3 mb-6">
                      <h4 className="text-lg font-bold text-slate-800">Generated Interview Guide</h4>
                      <span className="bg-indigo-50 text-indigo-600 text-xs font-bold px-2.5 py-1 rounded-md border border-indigo-100 uppercase">
                        {generatedQuestions.data.round_type}
                      </span>
                      <span className="bg-emerald-50 text-emerald-600 text-xs font-bold px-2.5 py-1 rounded-md border border-emerald-100 uppercase">
                        {generatedQuestions.data.difficulty}
                      </span>
                      <span className="bg-purple-50 text-purple-600 text-xs font-bold px-2.5 py-1 rounded-md border border-purple-100 uppercase">
                        {generatedQuestions.data.topic}
                      </span>
                    </div>

                    <div className="space-y-6">
                      {generatedQuestions.data.questions.map((q: any, i: number) => (
                        <div key={i} className="bg-slate-50 p-5 rounded-xl border border-slate-200">
                          <h5 className="font-semibold text-slate-900 mb-3 flex items-start gap-3">
                            <span className="bg-indigo-600 text-white w-6 h-6 rounded-full flex items-center justify-center text-xs shrink-0 mt-0.5">
                              {i + 1}
                            </span>
                            {q.question}
                          </h5>
                          
                          <div className="ml-9 space-y-3">
                            {q.reason_for_asking && (
                              <div>
                                <span className="text-xs font-bold text-slate-500 uppercase tracking-wider block mb-1">
                                  Why we ask this
                                </span>
                                <p className="text-sm text-slate-600">{q.reason_for_asking}</p>
                              </div>
                            )}
                            
                            {q.expected_answer_points && q.expected_answer_points.length > 0 && (
                              <div>
                                <span className="text-xs font-bold text-slate-500 uppercase tracking-wider block mb-1">
                                  What to look for
                                </span>
                                <ul className="list-disc pl-4 text-sm text-emerald-700 space-y-1">
                                  {q.expected_answer_points.map((pt: string, j: number) => (
                                    <li key={j}>{pt}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
