'use client';

import React, { useState } from 'react';
import { api } from '@/lib/api';
import { Card } from '@/components/ui/Card';
import { LoadingState } from '@/components/ui/LoadingState';
import { ErrorState } from '@/components/ui/ErrorState';
import { FileText, Copy, Check, Sparkles, PlusCircle } from 'lucide-react';
import Link from 'next/link';

interface JDData {
  job_title: string;
  department: string;
  location: string;
  employment_type: string;
  work_mode: string;
  experience_level: string;
  summary: string;
  responsibilities: string[];
  required_skills: string[];
  nice_to_have_skills: string[];
  qualifications: string[];
  benefits: string[];
  full_job_description: string;
}

interface JDResponse {
  status: string;
  generated_jd_id: string;
  job_id?: string;
  data: JDData;
}

export default function JDGeneratorPage() {
  // Form inputs
  const [role, setRole] = useState('');
  const [department, setDepartment] = useState('');
  const [experienceLevel, setExperienceLevel] = useState('MID');
  const [requiredSkills, setRequiredSkills] = useState('');
  const [niceToHaveSkills, setNiceToHaveSkills] = useState('');
  const [location, setLocation] = useState('');
  const [employmentType, setEmploymentType] = useState('FULL_TIME');
  const [workMode, setWorkMode] = useState('REMOTE');
  const [responsibilitiesHint, setResponsibilitiesHint] = useState('');
  const [saveToJob, setSaveToJob] = useState(false);

  // Result state
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<JDResponse | null>(null);
  const [copied, setCopied] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!role) {
      setError('Please fill in Job Role / Title.');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);
    setCopied(false);

    try {
      const payload = {
        role,
        department,
        experience_level: experienceLevel,
        required_skills: requiredSkills
          .split(',')
          .map((s) => s.trim())
          .filter((s) => s.length > 0),
        nice_to_have_skills: niceToHaveSkills
          .split(',')
          .map((s) => s.trim())
          .filter((s) => s.length > 0),
        location,
        employment_type: employmentType,
        work_mode: workMode,
        responsibilities_hint: responsibilitiesHint || null,
      };

      const response = await api.post('/assistant/generate-jd', payload, {
        params: { save_to_job: saveToJob },
      });

      setResult(response.data);
    } catch (err: any) {
      console.error(err);
      setError('Failed to generate job description using AI. Verify Gemini configuration.');
    } finally {
      setLoading(false);
    }
  };

  const handleCopyText = () => {
    if (result) {
      navigator.clipboard.writeText(result.data.full_job_description);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-extrabold tracking-tight text-slate-900 flex items-center gap-2.5">
          AI JD Generator
          <Sparkles className="text-indigo-400" size={24} />
        </h1>
        <p className="text-sm text-slate-400 mt-1.5">
          Compose structured and professional Job Descriptions customized for your openings using the Gemini LLM.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Generator Inputs */}
        <Card title="Job Opening Specifications" className="lg:col-span-5">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-[#424844] uppercase tracking-wider mb-2">
                Job Role / Title *
              </label>
              <input
                type="text"
                value={role}
                onChange={(e) => setRole(e.target.value)}
                className="w-full bg-white border border-[#e6e9e4] rounded-lg py-2 px-3 text-sm text-[#191c1a] focus:outline-none focus:border-[#476353] focus:ring-1 focus:ring-[#476353]"
                placeholder="Senior React Architect"
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-[#424844] uppercase tracking-wider mb-2">
                  Department
                </label>
                <input
                  type="text"
                  value={department}
                  onChange={(e) => setDepartment(e.target.value)}
                  className="w-full bg-white border border-[#e6e9e4] rounded-lg py-2 px-3 text-sm text-[#191c1a] focus:outline-none focus:border-[#476353] focus:ring-1 focus:ring-[#476353]"
                  placeholder="Engineering"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-[#424844] uppercase tracking-wider mb-2">
                  Location
                </label>
                <select
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
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
                <label className="block text-xs font-semibold text-[#424844] uppercase tracking-wider mb-2">
                  Employment Type
                </label>
                <select
                  value={employmentType}
                  onChange={(e) => setEmploymentType(e.target.value)}
                  className="w-full bg-white border border-[#e6e9e4] rounded-lg py-2 px-3 text-sm text-[#424844] focus:outline-none focus:border-[#476353] focus:ring-1 focus:ring-[#476353]"
                >
                  <option value="FULL_TIME">Full Time</option>
                  <option value="PART_TIME">Part Time</option>
                  <option value="CONTRACT">Contract</option>
                  <option value="INTERNSHIP">Internship</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-semibold text-[#424844] uppercase tracking-wider mb-2">
                  Work Mode
                </label>
                <select
                  value={workMode}
                  onChange={(e) => setWorkMode(e.target.value)}
                  className="w-full bg-white border border-[#e6e9e4] rounded-lg py-2 px-3 text-sm text-[#424844] focus:outline-none focus:border-[#476353] focus:ring-1 focus:ring-[#476353]"
                >
                  <option value="ONSITE">Onsite</option>
                  <option value="HYBRID">Hybrid</option>
                  <option value="REMOTE">Remote</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-[#424844] uppercase tracking-wider mb-2">
                Experience Level
              </label>
              <select
                value={experienceLevel}
                onChange={(e) => setExperienceLevel(e.target.value)}
                className="w-full bg-white border border-[#e6e9e4] rounded-lg py-2 px-3 text-sm text-[#424844] focus:outline-none focus:border-[#476353] focus:ring-1 focus:ring-[#476353]"
              >
                <option value="JUNIOR">Junior (Entry)</option>
                <option value="MID">Mid (Associate)</option>
                <option value="SENIOR">Senior (Lead)</option>
                <option value="EXECUTIVE">Executive</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-[#424844] uppercase tracking-wider mb-2">
                Required Skills (comma-separated)
              </label>
              <input
                type="text"
                value={requiredSkills}
                onChange={(e) => setRequiredSkills(e.target.value)}
                placeholder="React, TypeScript, Next.js"
                className="w-full bg-white border border-[#e6e9e4] rounded-lg py-2 px-3 text-sm text-[#191c1a] focus:outline-none focus:border-[#476353] focus:ring-1 focus:ring-[#476353]"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-[#424844] uppercase tracking-wider mb-2">
                Nice to Have Skills (comma-separated)
              </label>
              <input
                type="text"
                value={niceToHaveSkills}
                onChange={(e) => setNiceToHaveSkills(e.target.value)}
                placeholder="Docker, CI/CD, AWS"
                className="w-full bg-white border border-[#e6e9e4] rounded-lg py-2 px-3 text-sm text-[#191c1a] focus:outline-none focus:border-[#476353] focus:ring-1 focus:ring-[#476353]"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-[#424844] uppercase tracking-wider mb-2">
                Responsibilities Hints (Optional)
              </label>
              <textarea
                value={responsibilitiesHint}
                onChange={(e) => setResponsibilitiesHint(e.target.value)}
                rows={3}
                className="w-full bg-white border border-[#e6e9e4] rounded-lg py-2 px-3 text-sm text-[#191c1a] focus:outline-none focus:border-[#476353] focus:ring-1 focus:ring-[#476353]"
                placeholder="E.g., Lead migration from CRA to Next.js; optimize rendering."
              ></textarea>
            </div>

            <div className="flex items-center gap-2 pt-2">
              <input
                type="checkbox"
                id="saveToJob"
                checked={saveToJob}
                onChange={(e) => setSaveToJob(e.target.checked)}
                className="rounded border-[#223049] text-indigo-500 bg-[#f1f4f0] focus:ring-indigo-500 focus:ring-opacity-25 w-4 h-4 cursor-pointer"
              />
              <label htmlFor="saveToJob" className="text-xs font-semibold text-slate-300 cursor-pointer select-none">
                Save directly to Active Jobs database
              </label>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-650 hover:to-purple-750 text-white font-semibold py-3 rounded-lg shadow-lg hover:shadow-indigo-500/10 transition-all duration-200 active:scale-[0.98] disabled:opacity-55 flex items-center justify-center gap-2"
            >
              <Sparkles size={16} />
              {loading ? 'Generating...' : 'Generate Description'}
            </button>
          </form>
        </Card>

        {/* Generator Output */}
        <div className="lg:col-span-7 space-y-6">
          <Card title="Generated Description Output" className="min-h-[400px] flex flex-col justify-between">
            {loading && (
              <div className="py-20">
                <LoadingState type="page" message="Gemini AI is crafting your job description..." />
              </div>
            )}

            {!loading && !result && !error && (
              <div className="flex flex-col items-center justify-center py-24 text-slate-500 text-sm">
                <FileText size={48} className="text-slate-700 mb-4" />
                <p>Fill out the parameters and click Generate to see the description.</p>
              </div>
            )}

            {error && (
              <div className="py-12">
                <ErrorState message={error} />
              </div>
            )}

            {result && !loading && (
              <div className="space-y-6 animate-fadeIn">
                {/* Save Feedback */}
                {result.job_id && (
                  <div className="p-3.5 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 rounded-lg text-xs font-semibold flex items-center justify-between">
                    <span className="flex items-center gap-1.5">
                      <PlusCircle size={14} />
                      Saved directly as a Job!
                    </span>
                    <Link
                      href={`/jobs/${result.job_id}`}
                      className="bg-emerald-500 hover:bg-emerald-650 text-white font-bold px-3 py-1 rounded transition-colors text-center"
                    >
                      View Created Job
                    </Link>
                  </div>
                )}

                {/* Header Actions */}
                <div className="flex justify-end gap-2">
                  <button
                    onClick={handleCopyText}
                    className="inline-flex items-center gap-1.5 bg-slate-800 hover:bg-slate-700 text-xs font-semibold px-3 py-1.5 rounded-lg border border-border text-slate-200 transition-all active:scale-95"
                  >
                    {copied ? (
                      <>
                        <Check size={12} className="text-emerald-400" />
                        Copied
                      </>
                    ) : (
                      <>
                        <Copy size={12} />
                        Copy Markdown
                      </>
                    )}
                  </button>
                </div>

                {/* Structured Fields */}
                <div className="space-y-4 max-h-[500px] overflow-y-auto pr-2 border-t border-[#223049] pt-4">
                  <div>
                    <h4 className="text-sm font-bold text-slate-900">{result.data.job_title}</h4>
                    <p className="text-xs text-slate-400 mt-0.5">
                      {result.data.department} • {result.data.location} • {result.data.work_mode}
                    </p>
                  </div>

                  <div>
                    <h5 className="text-xs font-bold text-[#424844] uppercase tracking-wider mb-1.5">Role Summary</h5>
                    <p className="text-sm text-slate-300 leading-relaxed bg-[#f1f4f0] p-3 rounded-lg border border-border/40">
                      {result.data.summary}
                    </p>
                  </div>

                  {result.data.responsibilities?.length > 0 && (
                    <div>
                      <h5 className="text-xs font-bold text-[#424844] uppercase tracking-wider mb-1.5">Key Responsibilities</h5>
                      <ul className="list-disc pl-5 text-sm text-slate-300 space-y-1">
                        {result.data.responsibilities.map((r, idx) => (
                          <li key={idx} className="leading-relaxed">{r}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {result.data.required_skills?.length > 0 && (
                    <div>
                      <h5 className="text-xs font-bold text-[#424844] uppercase tracking-wider mb-1.5">Required Skill Set</h5>
                      <div className="flex flex-wrap gap-1.5">
                        {result.data.required_skills.map((s, idx) => (
                          <span key={idx} className="bg-indigo-500/10 text-indigo-400 text-xs px-2 py-0.5 rounded border border-indigo-500/20">
                            {s}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {result.data.qualifications?.length > 0 && (
                    <div>
                      <h5 className="text-xs font-bold text-[#424844] uppercase tracking-wider mb-1.5">Qualifications & Requirements</h5>
                      <ul className="list-disc pl-5 text-sm text-slate-300 space-y-1">
                        {result.data.qualifications.map((q, idx) => (
                          <li key={idx} className="leading-relaxed">{q}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
}
