'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import { DOMAIN_CATEGORIES } from '@/lib/constants';
import { Card } from '@/components/ui/Card';
import { Table, Thead, Tbody, Tr, Th, Td } from '@/components/ui/Table';
import { LoadingState } from '@/components/ui/LoadingState';
import { ErrorState } from '@/components/ui/ErrorState';
import { Search, UserPlus, SlidersHorizontal, Eye, Trash2 } from 'lucide-react';

interface Candidate {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  phone?: string;
  current_company?: string;
  current_location?: string;
  total_experience_years?: number;
  domain?: string;
  education_level?: string;
  notice_period?: string;
  skills?: string[];
  source?: string;
  created_at: string;
}

export default function CandidatesPage() {
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters State
  const [skillFilter, setSkillFilter] = useState('');
  const [locationFilter, setLocationFilter] = useState('');
  const [minExpFilter, setMinExpFilter] = useState('');
  const [maxExpFilter, setMaxExpFilter] = useState('');
  const [domainFilter, setDomainFilter] = useState('');
  const [educationFilter, setEducationFilter] = useState('');
  const [noticePeriodFilter, setNoticePeriodFilter] = useState('');

  // Manual Creation State
  const [showModal, setShowModal] = useState(false);
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [company, setCompany] = useState('');
  const [location, setLocation] = useState('');
  const [experience, setExperience] = useState('');
  const [domain, setDomain] = useState('');
  const [educationLevel, setEducationLevel] = useState('');
  const [noticePeriod, setNoticePeriod] = useState('');
  const [skillsCsv, setSkillsCsv] = useState('');
  const [createLoading, setCreateLoading] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);

  const fetchCandidates = async () => {
    setLoading(true);
    setError(null);
    try {
      const params: any = {
        skip: 0,
        limit: 100,
      };
      if (skillFilter.trim()) params.skill = skillFilter.trim();
      if (locationFilter.trim()) params.location = locationFilter.trim();
      if (domainFilter.trim()) params.domain = domainFilter.trim();
      if (educationFilter.trim()) params.education_level = educationFilter.trim();
      if (noticePeriodFilter.trim()) params.notice_period = noticePeriodFilter.trim();
      if (minExpFilter.trim()) {
        const val = parseFloat(minExpFilter);
        if (!isNaN(val)) params.min_experience = val;
      }
      if (maxExpFilter.trim()) {
        const val = parseFloat(maxExpFilter);
        if (!isNaN(val)) params.max_experience = val;
      }

      const response = await api.get('/candidates/', { params });
      setCandidates(response.data);
    } catch (err: any) {
      console.error(err);
      setError('Failed to retrieve candidates list.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCandidates();
  }, []);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchCandidates();
  };

  const handleClearFilters = () => {
    setSkillFilter('');
    setLocationFilter('');
    setMinExpFilter('');
    setMaxExpFilter('');
    setDomainFilter('');
    setEducationFilter('');
    setNoticePeriodFilter('');
    // Trigger fetch after clearing filters (we use timeout to let states flush)
    setTimeout(() => {
      fetchCandidates();
    }, 50);
  };

  const handleCreateCandidate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!firstName || !lastName || !email) {
      setCreateError('First Name, Last Name, and Email are required.');
      return;
    }

    setCreateLoading(true);
    setCreateError(null);

    try {
      const skillsArray = skillsCsv
        .split(',')
        .map((s) => s.trim())
        .filter((s) => s.length > 0);

      const payload = {
        first_name: firstName.trim(),
        last_name: lastName.trim(),
        email: email.trim(),
        phone: phone.trim() || undefined,
        current_company: company.trim() || undefined,
        current_location: location.trim() || undefined,
        total_experience_years: experience ? parseFloat(experience) : undefined,
        domain: domain || undefined,
        education_level: educationLevel.trim() || undefined,
        notice_period: noticePeriod.trim() || undefined,
        skills: skillsArray,
        source: 'MANUAL',
      };

      await api.post('/candidates/', payload);
      
      // Reset form
      setFirstName('');
      setLastName('');
      setEmail('');
      setPhone('');
      setCompany('');
      setLocation('');
      setExperience('');
      setDomain('');
      setEducationLevel('');
      setNoticePeriod('');
      setSkillsCsv('');
      setShowModal(false);

      // Refresh list
      fetchCandidates();
    } catch (err: any) {
      console.error(err);
      if (err.response && err.response.data && err.response.data.detail) {
        setCreateError(
          typeof err.response.data.detail === 'string'
            ? err.response.data.detail
            : 'Candidate creation failed. Email might already exist.'
        );
      } else {
        setCreateError('An error occurred during candidate registration.');
      }
    } finally {
      setCreateLoading(false);
    }
  };

  const handleDeleteCandidate = async (candidateId: string) => {
    if (window.confirm("Are you sure you want to delete this candidate? This action cannot be undone.")) {
      try {
        await api.delete(`/candidates/${candidateId}`);
        fetchCandidates();
      } catch (err: any) {
        console.error(err);
        alert(err.response?.data?.detail || "Failed to delete candidate.");
      }
    }
  };

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-slate-900">
            Candidates Directory
          </h1>
          <p className="text-sm text-slate-400 mt-1.5">
            Manage candidates, filter profiles, and review parsed resume details.
          </p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="inline-flex items-center gap-2 bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-650 hover:to-purple-750 text-white text-sm font-semibold px-4 py-2.5 rounded-lg shadow-lg hover:shadow-indigo-500/10 transition-all duration-200 active:scale-95 self-start sm:self-auto"
        >
          <UserPlus size={16} />
          Add Candidate
        </button>
      </div>

      {/* Filter and Search Bar */}
      <Card>
        <form onSubmit={handleSearchSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Skill */}
            <div className="relative">
              <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-slate-500 pointer-events-none">
                <Search size={16} />
              </span>
              <input
                type="text"
                value={skillFilter}
                onChange={(e) => setSkillFilter(e.target.value)}
                placeholder="Search by skill (e.g. Python)"
                className="w-full bg-white border border-[#e6e9e4] rounded-lg py-2 pl-9 pr-4 text-sm text-slate-900 placeholder-[#a0aba5] focus:outline-none focus:border-indigo-500 transition-colors duration-200"
              />
            </div>

            {/* Location */}
            <div className="relative">
              <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-slate-500 pointer-events-none">
                <SlidersHorizontal size={16} />
              </span>
              <input
                type="text"
                value={locationFilter}
                onChange={(e) => setLocationFilter(e.target.value)}
                placeholder="Search by location"
                className="w-full bg-white border border-[#e6e9e4] rounded-lg py-2 pl-9 pr-4 text-sm text-slate-900 placeholder-[#a0aba5] focus:outline-none focus:border-indigo-500 transition-colors duration-200"
              />
            </div>
            
            {/* Field / Domain */}
            <div className="relative">
              <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-slate-500 pointer-events-none">
                <SlidersHorizontal size={16} />
              </span>
              <select
                value={domainFilter}
                onChange={(e) => setDomainFilter(e.target.value)}
                className="w-full bg-white border border-[#e6e9e4] rounded-lg py-2 pl-9 pr-4 text-sm text-[#424844] focus:outline-none focus:border-[#476353] focus:ring-1 focus:ring-[#476353] appearance-none"
              >
                <option value="">All Domains</option>
                {DOMAIN_CATEGORIES.map(cat => (
                  <option key={cat} value={cat}>{cat.replace('_', ' ')}</option>
                ))}
              </select>
            </div>

            {/* Min Experience */}
            <div className="relative">
              <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-slate-500 pointer-events-none">
                <SlidersHorizontal size={16} />
              </span>
              <input
                type="number"
                value={minExpFilter}
                onChange={(e) => setMinExpFilter(e.target.value)}
                placeholder="Min experience in years"
                className="w-full bg-white border border-[#e6e9e4] rounded-lg py-2 pl-9 pr-4 text-sm text-slate-900 placeholder-[#a0aba5] focus:outline-none focus:border-indigo-500 transition-colors duration-200"
              />
            </div>

            {/* Max Experience */}
            <div className="relative">
              <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-slate-500 pointer-events-none">
                <SlidersHorizontal size={16} />
              </span>
              <input
                type="number"
                value={maxExpFilter}
                onChange={(e) => setMaxExpFilter(e.target.value)}
                placeholder="Max experience in years"
                className="w-full bg-white border border-[#e6e9e4] rounded-lg py-2 pl-9 pr-4 text-sm text-slate-900 placeholder-[#a0aba5] focus:outline-none focus:border-indigo-500 transition-colors duration-200"
              />
            </div>

            {/* Education Level */}
            <div className="relative">
              <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-slate-500 pointer-events-none">
                <SlidersHorizontal size={16} />
              </span>
              <select
                value={educationFilter}
                onChange={(e) => setEducationFilter(e.target.value)}
                className="w-full bg-white border border-[#e6e9e4] rounded-lg py-2 pl-9 pr-4 text-sm text-[#424844] focus:outline-none focus:border-indigo-500 transition-colors duration-200"
              >
                <option value="">Any Education Level</option>
                <option value="Bachelor's">Bachelor's</option>
                <option value="Master's">Master's</option>
                <option value="PhD">PhD</option>
                <option value="Other">Other</option>
              </select>
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={handleClearFilters}
              className="px-4 py-2 text-xs font-semibold text-slate-600 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition-colors"
            >
              Clear Filters
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-indigo-500 hover:bg-indigo-650 text-white text-xs font-semibold rounded-lg shadow transition-colors"
            >
              Apply Filters
            </button>
          </div>
        </form>
      </Card>

      {/* Candidates List View */}
      {loading ? (
        <LoadingState type="table" rows={6} message="Searching for candidates..." />
      ) : error ? (
        <ErrorState message={error} onRetry={fetchCandidates} />
      ) : candidates.length === 0 ? (
        <Card className="text-center py-12 text-slate-600">
          No candidates found. Try adjusting your search filters or add a new candidate profile.
        </Card>
      ) : (
        <Table>
          <Thead>
            <Tr>
              <Th>Name</Th>
              <Th>Contact Email</Th>
              <Th>Company & Location</Th>
              <Th>Experience</Th>
              <Th>Key Skills</Th>
              <Th className="text-right">Actions</Th>
            </Tr>
          </Thead>
          <Tbody>
            {candidates.map((cand) => (
              <Tr key={cand.id}>
                <Td className="font-semibold text-slate-900">
                  {cand.first_name} {cand.last_name}
                </Td>
                <Td className="text-slate-600">{cand.email}</Td>
                <Td className="text-slate-700">
                  {cand.current_company || 'N/A'}{' '}
                  {cand.current_location && (
                    <span className="text-slate-500 text-xs block mt-0.5">
                      📍 {cand.current_location}
                    </span>
                  )}
                </Td>
                <Td className="text-slate-700">
                  {cand.total_experience_years !== null && cand.total_experience_years !== undefined
                    ? `${cand.total_experience_years} years`
                    : 'N/A'}
                </Td>
                <Td>
                  <div className="flex flex-wrap gap-1 max-w-[300px]">
                    {cand.skills && cand.skills.length > 0 ? (
                      cand.skills.slice(0, 4).map((skill, idx) => (
                        <span
                          key={idx}
                          className="bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-[10px] font-medium px-2 py-0.5 rounded"
                        >
                          {skill}
                        </span>
                      ))
                    ) : (
                      <span className="text-slate-500 text-xs">No skills listed</span>
                    )}
                    {cand.skills && cand.skills.length > 4 && (
                      <span className="text-slate-500 text-[10px] font-medium px-1.5 py-0.5 self-center">
                        +{cand.skills.length - 4} more
                      </span>
                    )}
                  </div>
                </Td>
                <Td className="text-right">
                  <div className="inline-flex gap-2">
                    <Link
                      href={`/candidates/${cand.id}`}
                      className="inline-flex items-center gap-1.5 bg-slate-800 hover:bg-slate-700 text-xs font-semibold px-3 py-1.5 rounded-lg border border-border transition-colors text-slate-200"
                    >
                      <Eye size={12} />
                      View Details
                    </Link>
                    <button
                      onClick={() => handleDeleteCandidate(cand.id)}
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

      {/* Add Candidate Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <Card className="w-full max-w-lg shadow-2xl relative z-10 animate-scaleUp">
            <h3 className="text-xl font-bold text-[#191c1a] mb-4">Register Candidate Profile</h3>

            {createError && (
              <div className="mb-4 p-3 bg-rose-500/10 border border-rose-500/20 text-rose-400 rounded-lg text-sm font-medium">
                {createError}
              </div>
            )}

            <form onSubmit={handleCreateCandidate} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-[#424844] uppercase tracking-wider mb-1">
                    First Name *
                  </label>
                  <input
                    type="text"
                    value={firstName}
                    onChange={(e) => setFirstName(e.target.value)}
                    className="w-full bg-white border border-[#e6e9e4] rounded-lg py-2 px-3 text-sm text-[#191c1a] focus:outline-none focus:border-[#476353] focus:ring-1 focus:ring-[#476353]"
                    required
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-[#424844] uppercase tracking-wider mb-1">
                    Last Name *
                  </label>
                  <input
                    type="text"
                    value={lastName}
                    onChange={(e) => setLastName(e.target.value)}
                    className="w-full bg-white border border-[#e6e9e4] rounded-lg py-2 px-3 text-sm text-[#191c1a] focus:outline-none focus:border-[#476353] focus:ring-1 focus:ring-[#476353]"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-[#424844] uppercase tracking-wider mb-1">
                  Email Address *
                </label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full bg-white border border-[#e6e9e4] rounded-lg py-2 px-3 text-sm text-[#191c1a] focus:outline-none focus:border-[#476353] focus:ring-1 focus:ring-[#476353]"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-[#424844] uppercase tracking-wider mb-1">
                    Phone Number
                  </label>
                  <input
                    type="text"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    className="w-full bg-white border border-[#e6e9e4] rounded-lg py-2 px-3 text-sm text-[#191c1a] focus:outline-none focus:border-[#476353] focus:ring-1 focus:ring-[#476353]"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-[#424844] uppercase tracking-wider mb-1">
                    Total Experience (Years)
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    value={experience}
                    onChange={(e) => setExperience(e.target.value)}
                    className="w-full bg-white border border-[#e6e9e4] rounded-lg py-2 px-3 text-sm text-[#191c1a] focus:outline-none focus:border-[#476353] focus:ring-1 focus:ring-[#476353]"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-[#424844] uppercase tracking-wider mb-1">
                    Current Company
                  </label>
                  <input
                    type="text"
                    value={company}
                    onChange={(e) => setCompany(e.target.value)}
                    className="w-full bg-white border border-[#e6e9e4] rounded-lg py-2 px-3 text-sm text-[#191c1a] focus:outline-none focus:border-[#476353] focus:ring-1 focus:ring-[#476353]"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-[#424844] uppercase tracking-wider mb-1">
                    Current Location
                  </label>
                  <input
                    type="text"
                    value={location}
                    onChange={(e) => setLocation(e.target.value)}
                    className="w-full bg-white border border-[#e6e9e4] rounded-lg py-2 px-3 text-sm text-[#191c1a] focus:outline-none focus:border-[#476353] focus:ring-1 focus:ring-[#476353]"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                    Domain / Field
                  </label>
                  <select
                    value={domain}
                    onChange={(e) => setDomain(e.target.value)}
                    className="w-full bg-white border border-[#e6e9e4] rounded-lg py-2 px-3 text-sm text-slate-900 focus:outline-none focus:border-indigo-500 transition-colors"
                  >
                    <option value="">Auto-classify (Default)</option>
                    {DOMAIN_CATEGORIES.map(cat => (
                      <option key={cat} value={cat}>{cat.replace('_', ' ')}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-[#424844] uppercase tracking-wider mb-1">
                    Notice Period
                  </label>
                  <input
                    type="text"
                    value={noticePeriod}
                    onChange={(e) => setNoticePeriod(e.target.value)}
                    placeholder="e.g. 30 days"
                    className="w-full bg-white border border-[#e6e9e4] rounded-lg py-2 px-3 text-sm text-[#191c1a] focus:outline-none focus:border-[#476353] focus:ring-1 focus:ring-[#476353]"
                  />
                </div>
              </div>
              
              <div>
                <label className="block text-xs font-semibold text-[#424844] uppercase tracking-wider mb-1">
                  Education Level
                </label>
                <select
                  value={educationLevel}
                  onChange={(e) => setEducationLevel(e.target.value)}
                  className="w-full bg-white border border-[#e6e9e4] rounded-lg py-2 px-3 text-sm text-[#191c1a] focus:outline-none focus:border-[#476353] focus:ring-1 focus:ring-[#476353]"
                >
                  <option value="">Select Education Level</option>
                  <option value="Bachelor's">Bachelor's</option>
                  <option value="Master's">Master's</option>
                  <option value="PhD">PhD</option>
                  <option value="Other">Other</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-[#424844] uppercase tracking-wider mb-1">
                  Skills (comma-separated)
                </label>
                <input
                  type="text"
                  value={skillsCsv}
                  onChange={(e) => setSkillsCsv(e.target.value)}
                  placeholder="React, TypeScript, Node.js"
                  className="w-full bg-white border border-[#e6e9e4] rounded-lg py-2 px-3 text-sm text-[#191c1a] focus:outline-none focus:border-[#476353] focus:ring-1 focus:ring-[#476353]"
                />
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t border-[#e6e9e4] mt-6">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 text-sm font-semibold text-[#424844] hover:text-[#191c1a] hover:bg-[#f1f4f0] rounded-lg transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createLoading}
                  className="px-4 py-2 bg-[#476353] hover:bg-[#314d3e] text-white text-sm font-semibold rounded-lg shadow-sm active:scale-95 disabled:opacity-55 transition-colors"
                >
                  {createLoading ? 'Registering...' : 'Register Profile'}
                </button>
              </div>
            </form>
          </Card>
        </div>
      )}
    </div>
  );
}
