'use client';

import React, { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { Card } from '@/components/ui/Card';
import { LoadingState } from '@/components/ui/LoadingState';
import { ErrorState } from '@/components/ui/ErrorState';
import { Sparkles, HelpCircle, ChevronDown, ChevronUp, User, Briefcase, Plus } from 'lucide-react';

interface Candidate {
  id: string;
  first_name: string;
  last_name: string;
  skills?: string[];
}

interface Job {
  id: string;
  title: string;
  required_skills?: string[];
}

interface QuestionItem {
  question: string;
  expected_answer_points: string[];
  difficulty: string;
  reason_for_asking: string;
}

interface InterviewQuestionsResponse {
  status: string;
  generated_questions_id: string;
  data: {
    type: string;
    level: string;
    focus_skills: string[];
    questions: QuestionItem[];
  };
}

export default function InterviewQuestionsPage() {
  // Dropdowns lists
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [jobs, setJobs] = useState<Job[]>([]);

  // Form states
  const [selectedCandidateId, setSelectedCandidateId] = useState('');
  const [selectedJobId, setSelectedJobId] = useState('');
  const [skillsCsv, setSkillsCsv] = useState('');
  const [level, setLevel] = useState('MID');
  const [type, setType] = useState('TECHNICAL');
  const [numQuestions, setNumQuestions] = useState(5);

  // Result state
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<InterviewQuestionsResponse | null>(null);
  const [expandedQuestions, setExpandedQuestions] = useState<Record<number, boolean>>({});

  useEffect(() => {
    // Prefetch candidates and jobs lists for selection dropdowns
    const prefetchDropdowns = async () => {
      try {
        const [candRes, jobRes] = await Promise.all([
          api.get('/candidates/', { params: { limit: 100 } }),
          api.get('/jobs/', { params: { limit: 100 } })
        ]);
        setCandidates(candRes.data);
        setJobs(jobRes.data);
      } catch (err) {
        console.error('Failed to prefetch candidates or jobs for dropdown:', err);
      }
    };
    prefetchDropdowns();
  }, []);

  // Autofill skills if candidate changes
  const handleCandidateChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const cid = e.target.value;
    setSelectedCandidateId(cid);
    if (cid) {
      const selected = candidates.find((c) => c.id === cid);
      if (selected && selected.skills) {
        setSkillsCsv(selected.skills.join(', '));
      }
    }
  };

  // Autofill skills if job changes
  const handleJobChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const jid = e.target.value;
    setSelectedJobId(jid);
    if (jid) {
      const selected = jobs.find((j) => j.id === jid);
      if (selected && selected.required_skills) {
        // Append to existing or replace
        const newSkills = selected.required_skills.join(', ');
        setSkillsCsv((prev) => (prev ? `${prev}, ${newSkills}` : newSkills));
      }
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!skillsCsv.trim()) {
      setError('Please specify at least one skill or select a candidate/job profile.');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);
    setExpandedQuestions({});

    try {
      const skillsArray = skillsCsv
        .split(',')
        .map((s) => s.trim())
        .filter((s) => s.length > 0);

      const payload = {
        candidate_id: selectedCandidateId || null,
        job_id: selectedJobId || null,
        skills: skillsArray,
        level,
        type,
        number_of_questions: numQuestions,
      };

      const response = await api.post('/assistant/interview-questions', payload);
      setResult(response.data);
    } catch (err: any) {
      console.error(err);
      setError('Failed to generate interview questions. Verify Gemini settings.');
    } finally {
      setLoading(false);
    }
  };

  const toggleExpand = (idx: number) => {
    setExpandedQuestions((prev) => ({
      ...prev,
      [idx]: !prev[idx]
    }));
  };

  const getDifficultyBadge = (diff: string) => {
    const d = diff.toUpperCase();
    if (d === 'EASY') return 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400';
    if (d === 'HARD') return 'bg-rose-500/10 border-rose-500/20 text-rose-400';
    return 'bg-amber-500/10 border-amber-500/20 text-amber-400';
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-extrabold tracking-tight text-slate-900 flex items-center gap-2.5">
          Interview Assistant
          <Sparkles className="text-indigo-400" size={24} />
        </h1>
        <p className="text-sm text-slate-400 mt-1.5">
          Draft questions tailored for candidate skills, job requisites, and target experience levels.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Form panel */}
        <Card title="Tailoring Parameters" className="lg:col-span-5">
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Candidate Context */}
            <div>
              <label className="block text-xs font-semibold text-[#424844] uppercase tracking-wider mb-2">
                Select Candidate (Optional)
              </label>
              <div className="relative">
                <select
                  value={selectedCandidateId}
                  onChange={handleCandidateChange}
                  className="w-full bg-white border border-[#e6e9e4] rounded-lg py-2.5 px-3 text-sm text-[#424844] focus:outline-none focus:border-[#476353] focus:ring-1 focus:ring-[#476353]"
                >
                  <option value="">-- No Candidate Selected --</option>
                  {candidates.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.first_name} {c.last_name}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Job Context */}
            <div>
              <label className="block text-xs font-semibold text-[#424844] uppercase tracking-wider mb-2">
                Select Target Job (Optional)
              </label>
              <div className="relative">
                <select
                  value={selectedJobId}
                  onChange={handleJobChange}
                  className="w-full bg-white border border-[#e6e9e4] rounded-lg py-2.5 px-3 text-sm text-[#424844] focus:outline-none focus:border-[#476353] focus:ring-1 focus:ring-[#476353]"
                >
                  <option value="">-- No Job Selected --</option>
                  {jobs.map((j) => (
                    <option key={j.id} value={j.id}>
                      {j.title}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Skills */}
            <div>
              <label className="block text-xs font-semibold text-[#424844] uppercase tracking-wider mb-2">
                Evaluate Skills (comma-separated) *
              </label>
              <input
                type="text"
                value={skillsCsv}
                onChange={(e) => setSkillsCsv(e.target.value)}
                placeholder="React, TypeScript, Node.js"
                className="w-full bg-white border border-[#e6e9e4] rounded-lg py-2.5 px-3 text-sm text-slate-900 placeholder-[#a0aba5] focus:outline-none"
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-[#424844] uppercase tracking-wider mb-2">
                  Target Level
                </label>
                <select
                  value={level}
                  onChange={(e) => setLevel(e.target.value)}
                  className="w-full bg-white border border-[#e6e9e4] rounded-lg py-2 px-3 text-sm text-[#424844] focus:outline-none focus:border-[#476353] focus:ring-1 focus:ring-[#476353]"
                >
                  <option value="JUNIOR">Junior</option>
                  <option value="MID">Mid Level</option>
                  <option value="SENIOR">Senior</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-semibold text-[#424844] uppercase tracking-wider mb-2">
                  Question Type
                </label>
                <select
                  value={type}
                  onChange={(e) => setType(e.target.value)}
                  className="w-full bg-white border border-[#e6e9e4] rounded-lg py-2 px-3 text-sm text-[#424844] focus:outline-none focus:border-[#476353] focus:ring-1 focus:ring-[#476353]"
                >
                  <option value="TECHNICAL">Technical</option>
                  <option value="HR">HR / Fit</option>
                  <option value="MANAGERIAL">Managerial</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-[#424844] uppercase tracking-wider mb-2">
                Number of Questions
              </label>
              <input
                type="number"
                min="1"
                max="20"
                value={numQuestions}
                onChange={(e) => setNumQuestions(parseInt(e.target.value) || 5)}
                className="w-full bg-white border border-[#e6e9e4] rounded-lg py-2 px-3 text-sm text-[#191c1a] focus:outline-none focus:border-[#476353] focus:ring-1 focus:ring-[#476353]"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-650 hover:to-purple-750 text-white font-semibold py-3 rounded-lg shadow-lg hover:shadow-indigo-500/10 transition-all duration-200 active:scale-[0.98] disabled:opacity-55 flex items-center justify-center gap-2"
            >
              <Sparkles size={16} />
              {loading ? 'Composing Questions...' : 'Draft Interview Guide'}
            </button>
          </form>
        </Card>

        {/* Questions list */}
        <div className="lg:col-span-7 space-y-6">
          <Card title="Tailored Interview Questions Guide" className="min-h-[400px]">
            {loading && (
              <div className="py-20">
                <LoadingState type="page" message="Gemini AI is compiling custom questions..." />
              </div>
            )}

            {!loading && !result && !error && (
              <div className="flex flex-col items-center justify-center py-24 text-slate-500 text-sm">
                <HelpCircle size={48} className="text-slate-700 mb-4" />
                <p>Fill out the forms to generate tailored interview questions.</p>
              </div>
            )}

            {error && (
              <div className="py-12">
                <ErrorState message={error} />
              </div>
            )}

            {result && !loading && (
              <div className="space-y-4 animate-fadeIn">
                <div className="flex justify-between items-center text-xs text-slate-400 pb-3 border-b border-[#223049]">
                  <span>Focus: {result.data.focus_skills.join(', ')}</span>
                  <span className="font-bold text-indigo-400">{result.data.type} • {result.data.level}</span>
                </div>

                <div className="space-y-3.5 max-h-[500px] overflow-y-auto pr-2">
                  {result.data.questions.map((item, idx) => {
                    const isExpanded = !!expandedQuestions[idx];
                    return (
                      <div
                        key={idx}
                        className="bg-[#f1f4f0] border border-border/80 rounded-xl overflow-hidden hover:border-indigo-500/15 transition-all duration-200"
                      >
                        {/* Summary panel */}
                        <div
                          onClick={() => toggleExpand(idx)}
                          className="p-4 flex items-start justify-between gap-4 cursor-pointer select-none"
                        >
                          <div className="space-y-1.5">
                            <div className="flex items-center gap-2">
                              <span className="text-xs font-bold text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded">
                                Q{idx + 1}
                              </span>
                              <span className={`text-[10px] font-bold border px-2 py-0.5 rounded-full uppercase ${getDifficultyBadge(item.difficulty)}`}>
                                {item.difficulty}
                              </span>
                            </div>
                            <h4 className="text-sm font-semibold text-slate-200 leading-relaxed pr-2">
                              {item.question}
                            </h4>
                          </div>
                          <span className="text-slate-500 shrink-0 mt-1">
                            {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                          </span>
                        </div>

                        {/* Collapsible details */}
                        {isExpanded && (
                          <div className="p-4 border-t border-[#223049] bg-slate-900/15 space-y-4 animate-fadeIn">
                            <div>
                              <h5 className="text-[10px] font-bold text-[#424844] uppercase tracking-wider mb-1">
                                Rationale / Rationale for Asking
                              </h5>
                              <p className="text-xs text-slate-300 leading-relaxed">
                                {item.reason_for_asking}
                              </p>
                            </div>

                            <div>
                              <h5 className="text-[10px] font-bold text-[#424844] uppercase tracking-wider mb-2">
                                Expected Answer Points / Guidelines
                              </h5>
                              <ul className="list-disc pl-4 text-xs text-slate-300 space-y-1">
                                {item.expected_answer_points.map((pt, pidx) => (
                                  <li key={pidx} className="leading-relaxed">{pt}</li>
                                ))}
                              </ul>
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
}
