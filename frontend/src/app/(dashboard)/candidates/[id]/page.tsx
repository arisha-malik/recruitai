'use client';

import React, { useEffect, useState, use } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { DOMAIN_CATEGORIES } from '@/lib/constants';
import { Card } from '@/components/ui/Card';
import { LoadingState } from '@/components/ui/LoadingState';
import { ErrorState } from '@/components/ui/ErrorState';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { MatchScoreBadge } from '@/components/ui/MatchScoreBadge';
import { 
  User, 
  Mail, 
  Phone, 
  MapPin, 
  Building, 
  Calendar, 
  FileText, 
  Briefcase, 
  GraduationCap, 
  Award,
  ArrowLeft,
  Edit2,
  ChevronDown,
  ChevronUp,
  Trash2
} from 'lucide-react';

interface ResumeData {
  id: string;
  file_name: string;
  original_filename?: string;
  stored_filename?: string;
  storage_path?: string;
  candidate_primary_designation?: string;
  primary_skill?: string;
  parsing_status: string;
  created_at: string;
  parsed_data?: {
    full_name?: string;
    email?: string;
    mobile_number?: string;
    total_experience?: number;
    technical_skills?: string[];
    education?: any;
    certifications?: string[];
    current_company?: string;
    current_location?: string;
    notice_period?: string;
    work_experience?: any;
    projects?: any;
  };
}

interface CandidateDetails {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  phone?: string;
  current_company?: string;
  current_location?: string;
  total_experience_years?: number;
  domain?: string;
  skills?: string[];
  source?: string;
  created_at: string;
  resumes: ResumeData[];
}

interface Application {
  id: string;
  status: string;
  applied_at: string;
  job?: {
    id: string;
    title: string;
    department: string;
  };
  match_results?: {
    match_percentage: number;
    final_recommendation: string;
  }[];
}

// Reusable Collapsible Component
const CollapsibleItem = ({ title, subtitle, duration, children }: { title: string, subtitle?: string, duration?: string, children: React.ReactNode }) => {
  const [isOpen, setIsOpen] = useState(false);
  return (
    <div className="bg-white border border-[#e6e9e4] rounded-xl overflow-hidden shadow-sm transition-all">
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-4 bg-[#f9faf9] hover:bg-[#f1f4f0] transition-colors text-left"
      >
        <div className="pr-4">
          <h4 className="text-sm font-bold text-[#0F172A]">{title}</h4>
          {subtitle && <p className="text-xs text-[#334155] font-medium mt-0.5">{subtitle}</p>}
          {duration && <p className="text-xs text-[#64748B] mt-1 font-medium flex items-center gap-1"><Calendar size={12}/> {duration}</p>}
        </div>
        <div className="text-[#64748B]">
          {isOpen ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
        </div>
      </button>
      {isOpen && (
        <div className="p-4 border-t border-[#e6e9e4] bg-white text-sm text-[#334155] space-y-3">
          {children}
        </div>
      )}
    </div>
  );
};

export default function CandidateDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const candidateId = resolvedParams.id;
  const [candidate, setCandidate] = useState<CandidateDetails | null>(null);
  const [applications, setApplications] = useState<Application[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'profile' | 'experience' | 'education' | 'projects' | 'applications'>('profile');
  
  // Edit State
  const [isEditing, setIsEditing] = useState(false);
  const [editForm, setEditForm] = useState<Partial<CandidateDetails>>({});
  const [editLoading, setEditLoading] = useState(false);
  const [editError, setEditError] = useState<string | null>(null);

  // Delete State
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const router = useRouter();

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      // 1. Fetch Candidate Details
      const candRes = await api.get(`/candidates/${candidateId}`);
      setCandidate(candRes.data);

      // 2. Fetch Candidate Applications
      const appRes = await api.get('/applications/', {
        params: { candidate_id: candidateId }
      });
      setApplications(appRes.data);
    } catch (err: any) {
      console.error(err);
      setError(`Failed to load candidate profile details. Error: ${err.message || String(err)}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [candidateId]);

  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setEditLoading(true);
    setEditError(null);
    try {
      // Clean up the form data: remove relationships like resumes if they got in
      const payload = {
        first_name: editForm.first_name,
        last_name: editForm.last_name,
        email: editForm.email,
        phone: editForm.phone || null,
        current_company: editForm.current_company || null,
        current_location: editForm.current_location || null,
        total_experience_years: editForm.total_experience_years || null,
        domain: editForm.domain || null,
      };
      
      const res = await api.patch(`/candidates/${candidateId}`, payload);
      setCandidate(res.data);
      setIsEditing(false);
    } catch (err: any) {
      console.error(err);
      setEditError('Failed to update candidate profile.');
    } finally {
      setEditLoading(false);
    }
  };

  const openEditModal = () => {
    if (candidate) {
      setEditForm({
        first_name: candidate.first_name,
        last_name: candidate.last_name,
        email: candidate.email,
        phone: candidate.phone || '',
        current_company: candidate.current_company || '',
        current_location: candidate.current_location || '',
        total_experience_years: candidate.total_experience_years || 0,
        domain: candidate.domain || '',
      });
      setIsEditing(true);
    }
  };

  const handleDeleteCandidate = async () => {
    setDeleteLoading(true);
    try {
      await api.delete(`/candidates/${candidateId}`);
      router.push('/candidates');
    } catch (err: any) {
      console.error(err);
      alert('Failed to delete candidate. Please try again.');
      setDeleteLoading(false);
      setIsDeleting(false);
    }
  };

  if (loading) {
    return <LoadingState type="page" message="Loading candidate profile..." />;
  }

  if (error || !candidate) {
    const is404 = error?.includes('404');
    
    return (
      <div className="p-8 bg-rose-950/20 border border-rose-500/30 rounded-xl max-w-md mx-auto my-12 text-center shadow-md">
        <h1 className="text-xl font-bold text-rose-200 mb-2">
          {is404 ? 'Profile Not Found' : 'Something went wrong'}
        </h1>
        <p className="text-sm text-slate-300 mb-6 leading-relaxed">
          {is404 
            ? 'This candidate profile no longer exists. It may have been merged into an existing profile during AI parsing, or it was deleted.'
            : (error || 'Candidate profile not found')}
        </p>
        <div className="flex flex-col gap-3 justify-center">
          <Link 
            href="/candidates" 
            className="inline-flex items-center justify-center bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-medium px-4 py-2.5 rounded-lg border border-border transition-colors"
          >
            Return to Candidates List
          </Link>
          {!is404 && (
            <button onClick={fetchData} className="text-rose-400 text-xs hover:text-rose-300 transition-colors">
              Retry Request
            </button>
          )}
        </div>
      </div>
    );
  }

  // Get the most recent resume instead of the first one
  const resume = candidate.resumes && candidate.resumes.length > 0 
    ? [...candidate.resumes].sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())[0] 
    : null;
  const parsedData = resume?.parsed_data;

  // Helper to format custom work experience/education details
  const renderFormattedData = (data: any) => {
    if (!data || (Array.isArray(data) && data.length === 0)) return <p className="text-slate-500 text-sm italic">No additional details available.</p>;
    
    // If string, output directly
    if (typeof data === 'string') {
      return <p className="text-[#334155] text-sm whitespace-pre-line leading-relaxed">{data}</p>;
    }
    
    // If array, iterate through items
    if (Array.isArray(data)) {
      return (
        <div className="space-y-3">
          {data.map((item: any, idx: number) => {
            if (typeof item === 'string') {
              return <div key={idx} className="bg-[#f9faf9] border border-[#e6e9e4] rounded-lg p-3 text-sm text-[#334155] font-medium shadow-sm">{item}</div>;
            }
            
            // Standard JSON structure mappings
            const title = item.role || item.job_title || item.degree || item.qualification || item.title || item.name || 'Details';
            const subtitle = item.company || item.school || item.institution || item.university;
            const duration = item.duration || (item.start_date || item.start_year ? `${item.start_date || item.start_year} - ${item.end_date || item.end_year || 'Present'}` : undefined);
            
            // Determine if there is actually drill-down content to show
            const description = item.description || item.responsibilities || item.details;
            const hasTech = item.technologies || item.technologies_used;
            const hasAchievements = item.key_achievements;
            const cgpa = item.cgpa || item.percentage || item.marks;
            const fieldOfStudy = item.field_of_study || item.major;
            const hasExtraDetails = description || hasTech || hasAchievements || cgpa || item.location || item.links || item.key_features || fieldOfStudy;

            if (!hasExtraDetails) {
               // Render static block if no extra details
               return (
                 <div key={idx} className="bg-white border border-[#e6e9e4] rounded-xl p-4 shadow-sm">
                   <h4 className="text-sm font-bold text-[#0F172A]">{title}</h4>
                   {subtitle && <p className="text-xs text-[#334155] font-medium mt-0.5">{subtitle}</p>}
                   {duration && <p className="text-xs text-[#64748B] mt-1 font-medium flex items-center gap-1"><Calendar size={12}/> {duration}</p>}
                 </div>
               );
            }

            return (
              <CollapsibleItem key={idx} title={title} subtitle={subtitle} duration={duration}>
                {description && (
                  <div>
                    <span className="font-semibold text-[#0F172A] block mb-1">Description</span>
                    <p className="whitespace-pre-line leading-relaxed text-[#334155]">{description}</p>
                  </div>
                )}
                {hasTech && hasTech.length > 0 && (
                  <div className="mt-2">
                    <span className="font-semibold text-[#0F172A] block mb-1">Technologies</span>
                    <div className="flex flex-wrap gap-1.5">
                      {hasTech.map((t: string, i: number) => (
                        <span key={i} className="px-2 py-0.5 bg-[#476353]/10 text-[#476353] border border-[#476353]/20 text-xs rounded font-medium">{t}</span>
                      ))}
                    </div>
                  </div>
                )}
                {hasAchievements && hasAchievements.length > 0 && (
                  <div className="mt-2">
                    <span className="font-semibold text-[#0F172A] block mb-1">Key Achievements</span>
                    <ul className="list-disc pl-4 space-y-1 text-[#334155]">
                      {hasAchievements.map((a: string, i: number) => (
                        <li key={i}>{a}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {item.key_features && item.key_features.length > 0 && (
                  <div className="mt-2">
                    <span className="font-semibold text-[#0F172A] block mb-1">Key Features</span>
                    <ul className="list-disc pl-4 space-y-1 text-[#334155]">
                      {item.key_features.map((f: string, i: number) => (
                        <li key={i}>{f}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {cgpa && (
                  <p className="mt-2"><span className="font-semibold text-[#0F172A]">CGPA/Marks:</span> {cgpa}</p>
                )}
                {fieldOfStudy && (
                  <p className="mt-1"><span className="font-semibold text-[#0F172A]">Field of Study:</span> {fieldOfStudy}</p>
                )}
                {item.location && (
                  <p className="mt-1"><span className="font-semibold text-[#0F172A]">Location:</span> {item.location}</p>
                )}
                {item.links && item.links.length > 0 && (
                  <div className="mt-2">
                    <span className="font-semibold text-[#0F172A] block mb-1">Links</span>
                    <div className="flex flex-col gap-1">
                      {item.links.map((link: string, i: number) => (
                        <a key={i} href={link.startsWith('http') ? link : `https://${link}`} target="_blank" rel="noreferrer" className="text-indigo-600 hover:underline break-all">
                          {link}
                        </a>
                      ))}
                    </div>
                  </div>
                )}
              </CollapsibleItem>
            );
          })}
        </div>
      );
    }
    
    // Fallback JSON
    return (
      <pre className="bg-[#f9faf9] border border-[#e6e9e4] p-4 rounded-lg text-xs overflow-x-auto text-[#334155]">
        {JSON.stringify(data, null, 2)}
      </pre>
    );
  };

  return (
    <div className="space-y-8">
      {/* Back Button */}
      <div className="flex items-center justify-between">
        <Link
          href="/candidates"
          className="inline-flex items-center gap-2 text-sm font-semibold text-slate-400 hover:text-slate-200 transition-colors"
        >
          <ArrowLeft size={16} />
          Back to Candidates
        </Link>
        {resume && (
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400">Resume: {resume.file_name}</span>
            <StatusBadge status={resume.parsing_status} />
          </div>
        )}
      </div>

      {/* Profile Summary Card */}
      <Card className="bg-gradient-to-br from-[#161e31] to-[#121927]">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="flex items-center gap-4.5">
            <div className="w-16 h-16 rounded-full bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
              <User size={32} />
            </div>
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
                  {candidate.first_name} {candidate.last_name}
                </h1>
                <div className="flex items-center gap-1">
                  <button
                    onClick={openEditModal}
                    className="p-1.5 text-slate-400 hover:text-indigo-400 hover:bg-indigo-500/10 rounded-md transition-colors"
                    title="Edit Profile"
                  >
                    <Edit2 size={16} />
                  </button>
                  <button
                    onClick={() => setIsDeleting(true)}
                    className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 rounded-md transition-colors"
                    title="Delete Candidate"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
              <p className="text-sm text-indigo-400 mt-1">
                {candidate.current_company ? `Current: ${candidate.current_company}` : 'No current company listed'}
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-1 gap-3.5 text-sm text-slate-400 border-t md:border-t-0 md:border-l border-border pt-4 md:pt-0 md:pl-6">
            <div className="flex items-center gap-2">
              <Mail size={16} className="text-slate-500" />
              <span>{candidate.email}</span>
            </div>
            <div className="flex items-center gap-2">
              <Phone size={16} className="text-slate-500" />
              <span>{candidate.phone || 'No phone number'}</span>
            </div>
            <div className="flex items-center gap-2">
              <MapPin size={16} className="text-slate-500" />
              <span>{candidate.current_location || 'Location unspecified'}</span>
            </div>
          </div>
        </div>
      </Card>

      {/* Tabs Navigation */}
      <div className="flex border-b border-border overflow-x-auto gap-2">
        {(['profile', 'experience', 'education', 'projects', 'applications'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-5 py-3 border-b-2 font-bold text-sm transition-colors whitespace-nowrap ${
              activeTab === tab
                ? 'border-indigo-500 text-indigo-400 bg-indigo-500/5'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
          </button>
        ))}
      </div>

      {/* Tab Panels */}
      <div className="space-y-6">
        {/* Tab 1: Profile Summary */}
        {activeTab === 'profile' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Core Info */}
            <Card title="Candidate Details" className="lg:col-span-1 space-y-4">
              <div className="space-y-3.5">
                <div className="flex items-center justify-between py-1 border-b border-border/50 text-sm">
                  <span className="text-slate-400">Total Experience</span>
                  <span className="font-semibold text-slate-200">
                    {candidate.total_experience_years !== null ? `${candidate.total_experience_years} Years` : 'N/A'}
                  </span>
                </div>
                <div className="flex items-center justify-between py-1 border-b border-border/50 text-sm">
                  <span className="text-slate-400">Source</span>
                  <span className="font-semibold text-slate-200 uppercase text-xs">{candidate.source || 'Direct'}</span>
                </div>
                <div className="flex items-center justify-between py-1 border-b border-border/50 text-sm">
                  <span className="text-slate-400">Domain / Field</span>
                  <span className="font-semibold text-slate-200 uppercase text-xs">{candidate.domain || 'Auto-classify'}</span>
                </div>
                {parsedData?.notice_period && (
                  <div className="flex items-center justify-between py-1 border-b border-border/50 text-sm">
                    <span className="text-slate-400">Notice Period</span>
                    <span className="font-semibold text-slate-200">{parsedData.notice_period}</span>
                  </div>
                )}
              </div>
              
              {resume && (
                <div className="mt-6 pt-4 border-t border-border/50 space-y-3.5">
                  <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Resume Storage Details</h4>
                  <div className="flex flex-col gap-1 py-1 border-b border-border/50 text-sm">
                    <span className="text-slate-400 text-xs">Original Filename</span>
                    <span className="font-semibold text-slate-200 break-all">{resume.original_filename || resume.file_name}</span>
                  </div>
                  {(resume.stored_filename || resume.storage_path) && (
                    <>
                      <div className="flex flex-col gap-1 py-1 border-b border-border/50 text-sm">
                        <span className="text-slate-400 text-xs">Stored Filename</span>
                        <span className="font-semibold text-slate-200 break-all">{resume.stored_filename}</span>
                      </div>
                      <div className="flex flex-col gap-1 py-1 border-b border-border/50 text-sm">
                        <span className="text-slate-400 text-xs">Storage Path / Key</span>
                        <span className="font-semibold text-slate-200 break-all text-xs font-mono bg-slate-800/50 p-1.5 rounded">{resume.storage_path || resume.s3_key}</span>
                      </div>
                      <div className="flex flex-col gap-1 py-1 border-b border-border/50 text-sm">
                        <span className="text-slate-400 text-xs">Main Designation / Primary Skill</span>
                        <span className="font-semibold text-slate-200">
                          {resume.candidate_primary_designation || resume.primary_skill || 'N/A'}
                        </span>
                      </div>
                    </>
                  )}
                </div>
              )}
            </Card>

            {/* Skills */}
            <Card title="Key Skills Directory" className="lg:col-span-2 space-y-4">
              <div>
                <h4 className="text-xs font-semibold text-[#424844] uppercase tracking-wider mb-3">Skills List</h4>
                <div className="flex flex-wrap gap-2">
                  {candidate.skills && candidate.skills.length > 0 ? (
                    candidate.skills.map((skill, idx) => (
                      <span
                        key={idx}
                        className="bg-indigo-500/10 border border-indigo-500/25 text-indigo-400 text-xs font-semibold px-3 py-1.5 rounded-lg"
                      >
                        {skill}
                      </span>
                    ))
                  ) : (
                    <span className="text-slate-500 text-sm">No skills cataloged on profile.</span>
                  )}
                </div>
              </div>

              {parsedData?.technical_skills && parsedData.technical_skills.length > 0 && (
                <div className="pt-4 border-t border-[#223049]">
                  <h4 className="text-xs font-semibold text-[#424844] uppercase tracking-wider mb-3">Extracted Technical Skills</h4>
                  <div className="flex flex-wrap gap-2">
                    {parsedData.technical_skills.map((skill, idx) => (
                      <span
                        key={idx}
                        className="bg-purple-500/10 border border-purple-500/25 text-purple-400 text-xs font-semibold px-3 py-1.5 rounded-lg"
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </Card>
          </div>
        )}

        {/* Tab 2: Work Experience */}
        {activeTab === 'experience' && (
          <Card title="Work Experience Chronology">
            {parsedData ? renderFormattedData(parsedData.work_experience) : (
              <p className="text-slate-500 text-sm">Resume parsing data must be loaded to review work experience details.</p>
            )}
          </Card>
        )}

        {/* Tab 3: Education */}
        {activeTab === 'education' && (
          <Card title="Education & Academic Qualifications">
            {parsedData ? renderFormattedData(parsedData.education) : (
              <p className="text-slate-500 text-sm">Resume parsing data must be loaded to review academic history.</p>
            )}
          </Card>
        )}

        {/* Tab 4: Projects & Certifications */}
        {activeTab === 'projects' && (
          <div className="space-y-6">
            <Card title="Personal & Professional Projects">
              {parsedData ? renderFormattedData(parsedData.projects) : (
                <p className="text-slate-500 text-sm">Resume parsing data must be loaded to review project details.</p>
              )}
            </Card>

            {parsedData?.certifications && parsedData.certifications.length > 0 && (
              <Card title="Certifications">
                <ul className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {parsedData.certifications.map((cert, idx) => (
                    <li key={idx} className="flex items-center gap-3 bg-[#f1f4f0] border border-border p-3.5 rounded-xl text-[#334155] text-sm font-medium">
                      <Award className="text-indigo-400 shrink-0" size={18} />
                      {cert}
                    </li>
                  ))}
                </ul>
              </Card>
            )}
          </div>
        )}

        {/* Tab 5: Applications */}
        {activeTab === 'applications' && (
          <Card title="Applied Job Roles">
            {applications.length === 0 ? (
              <div className="text-center py-8 text-slate-500 text-sm">
                No active applications logged for this candidate.
              </div>
            ) : (
              <div className="space-y-4">
                {applications.map((app) => {
                  const match = app.match_results && app.match_results.length > 0 ? app.match_results[0] : null;
                  return (
                    <div
                      key={app.id}
                      className="bg-slate-900/30 border border-border rounded-xl p-5 flex flex-col md:flex-row md:items-center justify-between gap-4 hover:border-indigo-500/20 transition-all duration-200"
                    >
                      <div>
                        <h4 className="text-base font-bold text-slate-100">
                          {app.job?.title || 'Job Title Missing'}
                        </h4>
                        <p className="text-xs text-slate-400 mt-1">
                          Department: {app.job?.department || 'N/A'} • Applied: {new Date(app.applied_at).toLocaleDateString()}
                        </p>
                      </div>

                      <div className="flex items-center gap-4.5 self-start md:self-auto">
                        <StatusBadge status={app.status} />
                        {match && (
                          <MatchScoreBadge score={Math.round(match.match_percentage)} size="sm" />
                        )}
                        <Link
                          href={`/jobs/${app.job?.id}`}
                          className="bg-slate-800 hover:bg-slate-700 text-xs font-semibold px-3 py-1.5 border border-border rounded-lg text-slate-300"
                        >
                          View Job Details
                        </Link>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </Card>
        )}
      </div>

      {/* Edit Profile Modal */}
      {isEditing && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="bg-[#121927] border border-[#223049] rounded-xl shadow-2xl w-full max-w-lg overflow-hidden">
            <div className="p-5 border-b border-[#223049] flex justify-between items-center">
              <h3 className="text-lg font-bold text-slate-100">Edit Profile</h3>
              <button
                onClick={() => setIsEditing(false)}
                className="text-slate-400 hover:text-slate-200 transition-colors"
              >
                ✕
              </button>
            </div>
            <div className="p-5">
              {editError && (
                <div className="mb-4 p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
                  {editError}
                </div>
              )}
              <form onSubmit={handleEditSubmit} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-[#424844] uppercase tracking-wider mb-1">
                      First Name
                    </label>
                    <input
                      type="text"
                      value={editForm.first_name || ''}
                      onChange={(e) => setEditForm({ ...editForm, first_name: e.target.value })}
                      className="w-full bg-white border border-[#e6e9e4] rounded-lg py-2 px-3 text-sm text-[#191c1a] focus:outline-none focus:border-[#476353] focus:ring-1 focus:ring-[#476353]"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-[#424844] uppercase tracking-wider mb-1">
                      Last Name
                    </label>
                    <input
                      type="text"
                      value={editForm.last_name || ''}
                      onChange={(e) => setEditForm({ ...editForm, last_name: e.target.value })}
                      className="w-full bg-white border border-[#e6e9e4] rounded-lg py-2 px-3 text-sm text-[#191c1a] focus:outline-none focus:border-[#476353] focus:ring-1 focus:ring-[#476353]"
                      required
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-[#424844] uppercase tracking-wider mb-1">
                    Email Address
                  </label>
                  <input
                    type="email"
                    value={editForm.email || ''}
                    onChange={(e) => setEditForm({ ...editForm, email: e.target.value })}
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
                      value={editForm.phone || ''}
                      onChange={(e) => setEditForm({ ...editForm, phone: e.target.value })}
                      className="w-full bg-white border border-[#e6e9e4] rounded-lg py-2 px-3 text-sm text-[#191c1a] focus:outline-none focus:border-[#476353] focus:ring-1 focus:ring-[#476353]"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-[#424844] uppercase tracking-wider mb-1">
                      Total Experience (Yrs)
                    </label>
                    <input
                      type="number"
                      step="0.5"
                      value={editForm.total_experience_years || ''}
                      onChange={(e) => setEditForm({ ...editForm, total_experience_years: parseFloat(e.target.value) || 0 })}
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
                      value={editForm.current_company || ''}
                      onChange={(e) => setEditForm({ ...editForm, current_company: e.target.value })}
                      className="w-full bg-white border border-[#e6e9e4] rounded-lg py-2 px-3 text-sm text-[#191c1a] focus:outline-none focus:border-[#476353] focus:ring-1 focus:ring-[#476353]"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-[#424844] uppercase tracking-wider mb-1">
                      Current Location
                    </label>
                    <input
                      type="text"
                      value={editForm.current_location || ''}
                      onChange={(e) => setEditForm({ ...editForm, current_location: e.target.value })}
                      className="w-full bg-white border border-[#e6e9e4] rounded-lg py-2 px-3 text-sm text-[#191c1a] focus:outline-none focus:border-[#476353] focus:ring-1 focus:ring-[#476353]"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-[#424844] uppercase tracking-wider mb-1">
                    Domain / Field
                  </label>
                  <select
                    value={editForm.domain || ''}
                    onChange={(e) => setEditForm({ ...editForm, domain: e.target.value })}
                    className="w-full bg-white border border-[#e6e9e4] rounded-lg py-2 px-3 text-sm text-[#191c1a] focus:outline-none focus:border-[#476353] focus:ring-1 focus:ring-[#476353]"
                  >
                    <option value="">Auto-classify (Default)</option>
                    {DOMAIN_CATEGORIES.map(cat => (
                      <option key={cat} value={cat}>{cat.replace('_', ' ')}</option>
                    ))}
                  </select>
                </div>

                <div className="flex justify-end gap-3 pt-4 border-t border-[#223049] mt-6">
                  <button
                    type="button"
                    onClick={() => setIsEditing(false)}
                    className="px-4 py-2 bg-[#223049] hover:bg-[#2c3d5a] text-slate-200 rounded-lg text-sm font-semibold transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={editLoading}
                    className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm font-semibold transition-colors disabled:opacity-50"
                  >
                    {editLoading ? 'Saving...' : 'Save Changes'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Delete Candidate Modal */}
      {isDeleting && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="w-full max-w-md bg-white rounded-2xl shadow-2xl overflow-hidden relative z-10 animate-scaleUp">
            <div className="p-6">
              <div className="w-12 h-12 rounded-full bg-rose-500/10 flex items-center justify-center text-rose-500 mb-4 mx-auto">
                <Trash2 size={24} />
              </div>
              <h3 className="text-xl font-bold text-[#0F172A] text-center mb-2">Delete Candidate?</h3>
              <p className="text-[#64748B] text-center text-sm leading-relaxed">
                Are you sure you want to delete this candidate profile? This will permanently remove their profile, parsed resumes, and any application matching records. This action cannot be undone.
              </p>
              <div className="flex gap-3 mt-6">
                <button
                  type="button"
                  onClick={() => setIsDeleting(false)}
                  className="flex-1 px-4 py-2 bg-[#f1f4f0] hover:bg-[#e6e9e4] text-[#334155] rounded-lg text-sm font-semibold transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleDeleteCandidate}
                  disabled={deleteLoading}
                  className="flex-1 px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white rounded-lg text-sm font-semibold transition-colors disabled:opacity-50 flex items-center justify-center"
                >
                  {deleteLoading ? 'Deleting...' : 'Yes, Delete'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
