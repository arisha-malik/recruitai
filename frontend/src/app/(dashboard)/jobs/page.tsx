'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import { DOMAIN_CATEGORIES } from '@/lib/constants';
import { Card } from '@/components/ui/Card';
import { Table, Thead, Tbody, Tr, Th, Td } from '@/components/ui/Table';
import { LoadingState } from '@/components/ui/LoadingState';
import { ErrorState } from '@/components/ui/ErrorState';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { Briefcase, Plus, Settings, Search, Sparkles, Trash2 } from 'lucide-react';

interface Job {
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

export default function JobsPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters State
  const [statusFilter, setStatusFilter] = useState('');
  const [domainFilter, setDomainFilter] = useState('');
  const [experienceLevelFilter, setExperienceLevelFilter] = useState('');
  const [searchQuery, setSearchQuery] = useState('');

  // Create Job Modal State
  const [showModal, setShowModal] = useState(false);
  const [title, setTitle] = useState('');
  const [department, setDepartment] = useState('');
  const [domain, setDomain] = useState('');
  const [location, setLocation] = useState('');
  const [employmentType, setEmploymentType] = useState('FULL_TIME');
  const [experienceLevel, setExperienceLevel] = useState('MID');
  const [description, setDescription] = useState('');
  const [requiredSkillsCsv, setRequiredSkillsCsv] = useState('');
  const [createLoading, setCreateLoading] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);

  // Autofill State
  const [showAutofill, setShowAutofill] = useState(false);
  const [rawJDText, setRawJDText] = useState('');
  const [autofillLoading, setAutofillLoading] = useState(false);


  const fetchJobs = async () => {
    setLoading(true);
    setError(null);
    try {
      const params: any = {
        skip: 0,
        limit: 100,
      };
      if (statusFilter) params.status = statusFilter;
      if (domainFilter.trim()) params.domain = domainFilter.trim();
      if (experienceLevelFilter) params.experience_level = experienceLevelFilter;
      if (searchQuery.trim()) params.search = searchQuery.trim();

      const response = await api.get('/jobs/', { params });
      setJobs(response.data);
    } catch (err: any) {
      console.error(err);
      setError('Failed to fetch job profiles directory.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJobs();
  }, [statusFilter]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchJobs();
  };

  const handleAutofill = async () => {
    if (!rawJDText.trim()) return;
    setAutofillLoading(true);
    setCreateError(null);
    try {
      const response = await api.post('/assistant/parse-raw-jd', { text: rawJDText });
      const data = response.data.data;
      if (data.title) setTitle(data.title);
      if (data.department) setDepartment(data.department);
      if (data.location) setLocation(data.location);
      if (data.employment_type) setEmploymentType(data.employment_type);
      if (data.experience_level) setExperienceLevel(data.experience_level);
      if (data.description) setDescription(data.description);
      if (data.required_skills && data.required_skills.length > 0) {
        setRequiredSkillsCsv(data.required_skills.join(', '));
      }
      setShowAutofill(false);
      setRawJDText('');
    } catch (err: any) {
      console.error(err);
      setCreateError('Failed to autofill job description. Please try again.');
    } finally {
      setAutofillLoading(false);
    }
  };

  const handleCreateJob = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title || !description) {
      setCreateError('Title and Description are required.');
      return;
    }

    setCreateLoading(true);
    setCreateError(null);

    try {
      const skillsArray = requiredSkillsCsv
        .split(',')
        .map((s) => s.trim())
        .filter((s) => s.length > 0);

      const jobData = {
        title,
        department: department || null,
        domain: domain || null,
        location: location || null,
        employment_type: employmentType,
        experience_level: experienceLevel || null,
        description,
        required_skills: skillsArray.length > 0 ? skillsArray : null,
        status: 'OPEN',
      };

      await api.post('/jobs/', jobData);

      // Reset
      setTitle('');
      setDepartment('');
      setDomain('');
      setLocation('');
      setEmploymentType('FULL_TIME');
      setExperienceLevel('');
      setDescription('');
      setRequiredSkillsCsv('');
      setShowModal(false);

      fetchJobs();
    } catch (err: any) {
      console.error(err);
      setCreateError('An error occurred during job creation.');
    } finally {
      setCreateLoading(false);
    }
  };

  const handleDeleteJob = async (jobId: string) => {
    if (window.confirm("Are you sure you want to delete this job? This action cannot be undone.")) {
      try {
        await api.delete(`/jobs/${jobId}`);
        fetchJobs();
      } catch (err: any) {
        console.error(err);
        alert(err.response?.data?.detail || "Failed to delete job.");
      }
    }
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-slate-900">
            Job Openings
          </h1>
          <p className="text-sm text-slate-500 mt-1.5">
            Manage your job descriptions, trigger matching pipelines, and review top candidates.
          </p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="inline-flex items-center gap-2 bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-650 hover:to-purple-750 text-white text-sm font-semibold px-4 py-2.5 rounded-lg shadow-lg hover:shadow-indigo-500/10 transition-all duration-200 active:scale-95 self-start sm:self-auto"
        >
          <Plus size={16} />
          Create Job
        </button>
      </div>

      {/* Filters Form */}
      <Card>
        <form onSubmit={handleSearchSubmit} className="grid grid-cols-1 md:grid-cols-5 gap-4 items-end">
          <div>
            <label className="block text-xs font-semibold text-[#424844] uppercase tracking-wider mb-2">
              Search Title
            </label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Job title..."
                className="w-full bg-white border border-[#e6e9e4] rounded-lg py-2 pl-9 pr-3 text-sm text-slate-900 placeholder-[#a0aba5] focus:outline-none focus:border-indigo-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-[#424844] uppercase tracking-wider mb-2">
              Status
            </label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="w-full bg-white border border-[#e6e9e4] rounded-lg py-2 px-3 text-sm text-[#424844] focus:outline-none focus:border-[#476353] focus:ring-1 focus:ring-[#476353]"
            >
              <option value="">All Statuses</option>
              <option value="DRAFT">Draft</option>
              <option value="OPEN">Open</option>
              <option value="CLOSED">Closed</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-[#424844] uppercase tracking-wider mb-2">
              Domain / Field
            </label>
            <select
              value={domainFilter}
              onChange={(e) => setDomainFilter(e.target.value)}
              className="w-full bg-white border border-[#e6e9e4] rounded-lg py-2 px-3 text-sm text-[#424844] focus:outline-none focus:border-[#476353] focus:ring-1 focus:ring-[#476353]"
            >
              <option value="">All Domains</option>
              {DOMAIN_CATEGORIES.map(cat => (
                <option key={cat} value={cat}>{cat.replace('_', ' ')}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-[#424844] uppercase tracking-wider mb-2">
              Experience
            </label>
            <select
              value={experienceLevelFilter}
              onChange={(e) => setExperienceLevelFilter(e.target.value)}
              className="w-full bg-white border border-[#e6e9e4] rounded-lg py-2 px-3 text-sm text-[#424844] focus:outline-none focus:border-[#476353] focus:ring-1 focus:ring-[#476353]"
            >
              <option value="">All Levels</option>
              <option value="JUNIOR">Junior</option>
              <option value="MID">Mid-Level</option>
              <option value="SENIOR">Senior</option>
              <option value="LEAD">Lead/Director</option>
            </select>
          </div>

          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => {
                setStatusFilter('');
                setDomainFilter('');
                setExperienceLevelFilter('');
                setSearchQuery('');
                setTimeout(() => fetchJobs(), 50);
              }}
              className="w-1/2 px-4 py-2 text-xs font-semibold text-slate-600 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition-colors border border-transparent"
            >
              Clear
            </button>
            <button
              type="submit"
              className="w-1/2 px-4 py-2 bg-indigo-500 hover:bg-indigo-650 text-white text-xs font-semibold rounded-lg shadow transition-colors"
            >
              Apply
            </button>
          </div>
        </form>
      </Card>

      {/* Jobs Table */}
      {loading ? (
        <LoadingState type="table" rows={4} message="Fetching jobs list..." />
      ) : error ? (
        <ErrorState message={error} onRetry={fetchJobs} />
      ) : jobs.length === 0 ? (
        <Card className="text-center py-12 text-slate-400">
          No job records found. Create one to get started.
        </Card>
      ) : (
        <Table>
          <Thead>
            <Tr>
              <Th>Job Title</Th>
              <Th>Domain</Th>
              <Th>Location</Th>
              <Th>Employment Mode</Th>
              <Th>Status</Th>
              <Th className="text-right">Actions</Th>
            </Tr>
          </Thead>
          <Tbody>
            {jobs.map((job) => (
              <Tr key={job.id}>
                <Td className="font-semibold text-slate-900">
                  <Link href={`/jobs/${job.id}`} className="hover:text-indigo-400 transition-colors">
                    {job.title}
                  </Link>
                </Td>
                <Td className="text-slate-600">
                  <span className="bg-indigo-50 text-indigo-700 text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider whitespace-nowrap">
                    {job.domain}
                  </span>
                </Td>
                <Td className="text-slate-600">{job.location}</Td>
                <Td className="text-slate-500 text-xs">
                  {job.employment_type.replace(/_/g, ' ')} • {job.experience_level}
                </Td>
                <Td>
                  <StatusBadge status={job.status} />
                </Td>
                <Td className="text-right">
                  <div className="inline-flex gap-2">
                    <Link
                      href={`/jobs/${job.id}`}
                      className="inline-flex items-center gap-1.5 bg-slate-100 hover:bg-slate-200 text-xs font-semibold px-3 py-1.5 rounded-lg border border-slate-200 transition-colors text-slate-700"
                    >
                      <Settings size={12} />
                      View Details
                    </Link>
                    <button
                      onClick={() => handleDeleteJob(job.id)}
                      className="inline-flex items-center gap-1.5 bg-rose-50 hover:bg-rose-100 text-xs font-semibold px-3 py-1.5 rounded-lg border border-rose-200 transition-colors text-rose-600"
                    >
                      <Trash2 size={12} />
                      Delete
                    </button>
                  </div>
                </Td>
              </Tr>
            ))}
          </Tbody>
        </Table>
      )}

      {/* Create Job Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <Card className="w-full max-w-xl shadow-2xl relative z-10 animate-scaleUp max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-bold text-slate-900">Create Job Profile</h3>
              <button
                type="button"
                onClick={() => setShowAutofill(!showAutofill)}
                className="flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 bg-indigo-50 text-indigo-600 hover:bg-indigo-100 rounded-lg transition-colors"
              >
                <Sparkles size={14} />
                Autofill
              </button>
            </div>

            {showAutofill && (
              <div className="mb-4 p-4 bg-slate-50 border border-slate-200 rounded-lg">
                <label className="block text-xs font-semibold text-[#424844] uppercase tracking-wider mb-2">
                  Paste Raw Job Description
                </label>
                <textarea
                  value={rawJDText}
                  onChange={(e) => setRawJDText(e.target.value)}
                  rows={4}
                  placeholder="Paste the full job description text here..."
                  className="w-full bg-white border border-[#e6e9e4] rounded-lg py-2 px-3 text-sm text-[#191c1a] focus:outline-none focus:border-[#476353] focus:ring-1 focus:ring-[#476353] resize-y mb-3"
                ></textarea>
                <div className="flex justify-end gap-2">
                  <button
                    type="button"
                    onClick={() => setShowAutofill(false)}
                    className="px-3 py-1.5 text-xs font-semibold text-slate-500 hover:bg-slate-200 rounded-lg transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    type="button"
                    onClick={handleAutofill}
                    disabled={autofillLoading || !rawJDText.trim()}
                    className="flex items-center gap-1.5 px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white text-xs font-semibold rounded-lg shadow-sm transition-colors"
                  >
                    {autofillLoading ? (
                      <span className="animate-pulse">Parsing...</span>
                    ) : (
                      <>
                        <Sparkles size={12} />
                        Process
                      </>
                    )}
                  </button>
                </div>
              </div>
            )}

            {createError && (
              <div className="mb-4 p-3 bg-rose-500/10 border border-rose-500/20 text-rose-400 rounded-lg text-sm font-medium">
                {createError}
              </div>
            )}

            <form onSubmit={handleCreateJob} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-[#424844] uppercase tracking-wider mb-1">
                  Job Title *
                </label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full bg-white border border-[#e6e9e4] rounded-lg py-2 px-3 text-sm text-[#191c1a] focus:outline-none focus:border-[#476353] focus:ring-1 focus:ring-[#476353] focus:border-indigo-500"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-[#424844] uppercase tracking-wider mb-1">
                    Domain / Field
                  </label>
                  <select
                    value={domain}
                    onChange={(e) => setDomain(e.target.value)}
                    className="w-full bg-white border border-[#e6e9e4] rounded-lg py-2 px-3 text-sm text-[#191c1a] focus:outline-none focus:border-[#476353] focus:ring-1 focus:ring-[#476353] focus:border-indigo-500"
                  >
                    <option value="">Auto-classify (Default)</option>
                    {DOMAIN_CATEGORIES.map(cat => (
                      <option key={cat} value={cat}>{cat.replace('_', ' ')}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-[#424844] uppercase tracking-wider mb-1">
                    Department
                  </label>
                  <input
                    type="text"
                    value={department}
                    onChange={(e) => setDepartment(e.target.value)}
                    className="w-full bg-white border border-[#e6e9e4] rounded-lg py-2 px-3 text-sm text-[#191c1a] focus:outline-none focus:border-[#476353] focus:ring-1 focus:ring-[#476353] focus:border-indigo-500"
                    placeholder="Engineering"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-[#424844] uppercase tracking-wider mb-1">
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
                  <label className="block text-xs font-semibold text-[#424844] uppercase tracking-wider mb-1">
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
                  <label className="block text-xs font-semibold text-[#424844] uppercase tracking-wider mb-1">
                    Experience Level
                  </label>
                  <select
                    value={experienceLevel}
                    onChange={(e) => setExperienceLevel(e.target.value)}
                    className="w-full bg-white border border-[#e6e9e4] rounded-lg py-2 px-3 text-sm text-[#424844] focus:outline-none focus:border-[#476353] focus:ring-1 focus:ring-[#476353]"
                  >
                    <option value="">Any / Open</option>
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
                  value={requiredSkillsCsv}
                  onChange={(e) => setRequiredSkillsCsv(e.target.value)}
                  placeholder="React, Next.js, Node.js"
                  className="w-full bg-white border border-[#e6e9e4] rounded-lg py-2 px-3 text-sm text-[#191c1a] focus:outline-none focus:border-[#476353] focus:ring-1 focus:ring-[#476353]"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-[#424844] uppercase tracking-wider mb-1">
                  Job Description *
                </label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  rows={4}
                  className="w-full bg-white border border-[#e6e9e4] rounded-lg py-2 px-3 text-sm text-[#191c1a] focus:outline-none focus:border-[#476353] focus:ring-1 focus:ring-[#476353] focus:border-indigo-500 resize-y"
                  required
                ></textarea>
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t border-[#223049] mt-6">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 text-sm font-semibold text-slate-400 hover:text-slate-200 hover:bg-slate-800/40 rounded-lg transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createLoading}
                  className="px-4 py-2 bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-650 hover:to-purple-750 text-white text-sm font-semibold rounded-lg shadow-lg active:scale-95 disabled:opacity-55"
                >
                  {createLoading ? 'Creating...' : 'Create Job'}
                </button>
              </div>
            </form>
          </Card>
        </div>
      )}
    </div>
  );
}
