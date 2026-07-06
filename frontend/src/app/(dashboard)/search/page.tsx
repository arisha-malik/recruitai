'use client';

import React, { useEffect, useState, Suspense } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { api } from '@/lib/api';
import { Card } from '@/components/ui/Card';
import { Table, Thead, Tbody, Tr, Th, Td } from '@/components/ui/Table';
import { LoadingState } from '@/components/ui/LoadingState';
import { ErrorState } from '@/components/ui/ErrorState';
import { Search, Eye, Filter } from 'lucide-react';

interface Candidate {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  current_company?: string;
  current_location?: string;
  total_experience_years?: number;
  skills?: string[];
}

function SearchResultsContent() {
  const searchParams = useSearchParams();
  const query = searchParams.get('q') || '';
  
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [filters, setFilters] = useState<any>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!query) {
      setLoading(false);
      return;
    }

    const fetchResults = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await api.get(`/search/candidates?q=${encodeURIComponent(query)}`);
        setCandidates(response.data.candidates || []);
        setFilters(response.data.filters_applied || {});
      } catch (err: any) {
        console.error(err);
        setError('Failed to fetch search results.');
      } finally {
        setLoading(false);
      }
    };

    fetchResults();
  }, [query]);

  if (loading) {
    return <LoadingState type="page" message="AI is analyzing the database to find the best candidates..." />;
  }

  if (error) {
    return <ErrorState message={error} />;
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col gap-4">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-slate-900 flex items-center gap-3">
            <Search className="w-8 h-8 text-indigo-500" />
            Search Results
          </h1>
          <p className="text-sm text-slate-500 mt-1.5">
            Showing candidates matching: <span className="font-semibold text-slate-700">"{query}"</span>
          </p>
        </div>
      </div>

      {/* AI Parsed Filters View */}
      {Object.keys(filters).length > 0 && (
        <Card className="bg-indigo-50/50 border-indigo-100 shadow-sm">
          <div className="flex items-start gap-4">
            <div className="p-2 bg-indigo-100 rounded-lg text-indigo-600 mt-1">
              <Filter className="w-5 h-5" />
            </div>
            <div className="flex-1">
              <h3 className="text-sm font-bold text-slate-800 mb-2">AI Extracted Parameters</h3>
              <div className="flex flex-wrap gap-x-6 gap-y-3 text-sm">
                {filters.skills && filters.skills.length > 0 && (
                  <div>
                    <span className="text-slate-500 text-xs uppercase tracking-wider font-semibold block mb-1">Skills</span>
                    <div className="flex flex-wrap gap-1.5">
                      {filters.skills.map((s: string) => (
                        <span key={s} className="px-2 py-0.5 bg-white border border-indigo-200 text-indigo-700 rounded-md text-xs font-medium">
                          {s}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                
                {filters.roles && filters.roles.length > 0 && (
                  <div>
                    <span className="text-slate-500 text-xs uppercase tracking-wider font-semibold block mb-1">Roles</span>
                    <div className="text-slate-700 font-medium">{filters.roles.join(', ')}</div>
                  </div>
                )}
                
                {filters.locations && filters.locations.length > 0 && (
                  <div>
                    <span className="text-slate-500 text-xs uppercase tracking-wider font-semibold block mb-1">Location</span>
                    <div className="text-slate-700 font-medium">{filters.locations.join(', ')}</div>
                  </div>
                )}
                
                {filters.min_experience_years !== null && filters.min_experience_years !== undefined && (
                  <div>
                    <span className="text-slate-500 text-xs uppercase tracking-wider font-semibold block mb-1">Experience</span>
                    <div className="text-slate-700 font-medium">{filters.min_experience_years}+ years</div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* Results Table */}
      <Card>
        <div className="mb-4">
          <h3 className="text-lg font-bold text-slate-900">Found {candidates.length} Candidate{candidates.length !== 1 ? 's' : ''}</h3>
        </div>

        {candidates.length === 0 ? (
          <div className="text-center py-10">
            <p className="text-slate-500">No candidates found matching your criteria. Try adjusting your search query.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <Table>
              <Thead>
                <Tr>
                  <Th>Candidate</Th>
                  <Th>Experience</Th>
                  <Th>Location</Th>
                  <Th>Skills Match</Th>
                  <Th className="text-right">Actions</Th>
                </Tr>
              </Thead>
              <Tbody>
                {candidates.map((candidate) => (
                  <Tr key={candidate.id} className="hover:bg-slate-50/50 transition-colors">
                    <Td className="font-semibold text-slate-900">
                      {candidate.first_name} {candidate.last_name}
                      {candidate.current_company && (
                        <div className="text-xs text-slate-500 font-normal mt-0.5">{candidate.current_company}</div>
                      )}
                    </Td>
                    <Td className="text-slate-600">
                      {candidate.total_experience_years !== undefined && candidate.total_experience_years !== null
                        ? `${candidate.total_experience_years} years`
                        : '-'}
                    </Td>
                    <Td className="text-slate-600 capitalize">
                      {candidate.current_location || '-'}
                    </Td>
                    <Td>
                      <div className="flex flex-wrap gap-1">
                        {candidate.skills && candidate.skills.slice(0, 3).map((skill, i) => (
                          <span key={i} className="text-[10px] px-2 py-0.5 bg-slate-100 text-slate-600 rounded border border-slate-200">
                            {skill}
                          </span>
                        ))}
                        {candidate.skills && candidate.skills.length > 3 && (
                          <span className="text-[10px] px-2 py-0.5 bg-slate-50 text-slate-600 rounded border border-slate-100">
                            +{candidate.skills.length - 3}
                          </span>
                        )}
                      </div>
                    </Td>
                    <Td className="text-right">
                      <Link
                        href={`/candidates/${candidate.id}`}
                        className="inline-flex items-center gap-1.5 bg-white hover:bg-slate-50 text-xs font-semibold px-3 py-1.5 rounded-lg border border-slate-200 transition-colors text-slate-700"
                      >
                        <Eye size={12} />
                        View Profile
                      </Link>
                    </Td>
                  </Tr>
                ))}
              </Tbody>
            </Table>
          </div>
        )}
      </Card>
    </div>
  );
}

export default function SearchResultsPage() {
  return (
    <Suspense fallback={<LoadingState type="page" message="Loading..." />}>
      <SearchResultsContent />
    </Suspense>
  );
}
