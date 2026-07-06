'use client';

import React, { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { Card } from '@/components/ui/Card';
import { Table, Thead, Tbody, Tr, Th, Td } from '@/components/ui/Table';
import { LoadingState } from '@/components/ui/LoadingState';
import { ErrorState } from '@/components/ui/ErrorState';
import { BarChart3, Database, PieChart, Users, Clock, History } from 'lucide-react';

interface FunnelData {
  status_counts: Record<string, number>;
  status_percentages: Record<string, number>;
}

interface ParsingStats {
  total_uploaded: number;
  parsed_count: number;
  failed_count: number;
  success_rate: number;
}

interface MatchingStats {
  average_score: number;
  fit_bands: Record<string, number>;
  recommendations: Record<string, number>;
}

interface SourceData {
  source: string;
  count: number;
  shortlisted_count: number;
  shortlist_rate: number;
}

interface TimeToHireData {
  average_days_to_hire?: number;
  average_days_to_interview?: number;
  stage_durations?: Record<string, number>;
}

interface LogEvent {
  id: string;
  event_type: string;
  created_at: string;
  actor_id?: string;
  candidate_id?: string;
  job_id?: string;
  details?: any;
}

export default function AnalyticsPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // States
  const [funnel, setFunnel] = useState<FunnelData | null>(null);
  const [parsing, setParsing] = useState<ParsingStats | null>(null);
  const [matching, setMatching] = useState<MatchingStats | null>(null);
  const [sources, setSources] = useState<SourceData[]>([]);
  const [timeToHire, setTimeToHire] = useState<TimeToHireData | null>(null);
  const [events, setEvents] = useState<LogEvent[]>([]);

  const fetchAnalytics = async () => {
    setLoading(true);
    setError(null);
    try {
      const [funnelRes, parsingRes, matchingRes, sourcesRes, timeRes, eventsRes] = await Promise.all([
        api.get('/analytics/candidate-pipeline'),
        api.get('/analytics/resume-parsing'),
        api.get('/analytics/matching'),
        api.get('/analytics/source-effectiveness'),
        api.get('/analytics/time-to-hire'),
        api.get('/analytics/events', { params: { limit: 20 } })
      ]);

      setFunnel(funnelRes.data);
      setParsing(parsingRes.data);
      setMatching(matchingRes.data);
      setSources(sourcesRes.data.sources || []);
      setTimeToHire(timeRes.data);
      setEvents(eventsRes.data.events || []);
    } catch (err: any) {
      console.error(err);
      setError('Failed to fetch analytics metrics. Ensure database events exist.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, []);

  if (loading) {
    return <LoadingState type="page" message="Compiling platform metrics & audit logs..." />;
  }

  if (error) {
    return <ErrorState message={error} onRetry={fetchAnalytics} />;
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-extrabold tracking-tight text-slate-900 flex items-center gap-2.5">
          Platform Analytics
          <BarChart3 className="text-indigo-400" size={24} />
        </h1>
        <p className="text-sm text-slate-400 mt-1.5">
          Insights on hiring funnel efficiency, sourcing channels, and parsing accuracies.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Candidate Pipeline Funnel */}
        <Card title="Candidate Pipeline Funnel" className="flex flex-col justify-between">
          <div className="space-y-3.5 my-2">
            {funnel && funnel.status_counts && Object.keys(funnel.status_counts).length > 0 ? (
              Object.entries(funnel.status_counts).map(([stage, count]) => {
                const percent = Math.round(funnel.status_percentages[stage] || 0);
                return (
                  <div key={stage} className="space-y-1">
                    <div className="flex justify-between items-center text-xs">
                      <span className="font-semibold text-slate-300">{stage}</span>
                      <span className="text-slate-400">{count} Candidates ({percent}%)</span>
                    </div>
                    {/* Visual bar */}
                    <div className="w-full bg-[#f1f4f0] h-2.5 rounded-full overflow-hidden border border-border/30">
                      <div
                        className="bg-gradient-to-r from-indigo-500 to-purple-600 h-full rounded-full"
                        style={{ width: `${percent}%` }}
                      ></div>
                    </div>
                  </div>
                );
              })
            ) : (
              <p className="text-slate-500 text-sm text-center py-6">No funnel statistics available.</p>
            )}
          </div>
        </Card>

        {/* AI Matching Distribution */}
        <Card title="AI Matching Distributions" className="flex flex-col justify-between">
          <div className="space-y-3.5 my-2">
            {matching && matching.fit_bands && Object.keys(matching.fit_bands).length > 0 ? (
              Object.entries(matching.fit_bands).map(([band, count]) => {
                // Map band to color
                const getBandColor = (b: string) => {
                  if (b.toLowerCase().includes('excellent') || b.toLowerCase().includes('strong')) return 'bg-emerald-500';
                  if (b.toLowerCase().includes('good') || b.toLowerCase().includes('mid')) return 'bg-indigo-500';
                  if (b.toLowerCase().includes('fair') || b.toLowerCase().includes('maybe')) return 'bg-amber-500';
                  return 'bg-rose-500';
                };
                return (
                  <div key={band} className="flex justify-between items-center py-2.5 border-b border-border/40 text-sm">
                    <div className="flex items-center gap-2">
                      <span className={`w-3 h-3 rounded-full ${getBandColor(band)}`}></span>
                      <span className="font-semibold text-slate-300">{band} Fit</span>
                    </div>
                    <span className="font-bold text-slate-200">{count} Profiles</span>
                  </div>
                );
              })
            ) : (
              <p className="text-slate-500 text-sm text-center py-6">No matching evaluations performed yet.</p>
            )}
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Resume parsing accuracy */}
        <Card title="Resume Parsing Performance" className="flex flex-col justify-between">
          {parsing ? (
            <div className="space-y-4 my-2 text-sm">
              <div className="flex justify-between items-center py-1.5 border-b border-border/50">
                <span className="text-slate-400">Total Uploaded</span>
                <span className="font-bold text-slate-200">{parsing.total_uploaded}</span>
              </div>
              <div className="flex justify-between items-center py-1.5 border-b border-border/50">
                <span className="text-slate-400">Successfully Parsed</span>
                <span className="font-bold text-emerald-400">{parsing.parsed_count}</span>
              </div>
              <div className="flex justify-between items-center py-1.5 border-b border-border/50">
                <span className="text-slate-400">Parsing Failures</span>
                <span className="font-bold text-rose-400">{parsing.failed_count}</span>
              </div>
              <div className="bg-[#f1f4f0] border border-border/60 p-4 rounded-xl flex items-center justify-between mt-4">
                <div className="space-y-0.5">
                  <p className="text-[10px] text-slate-400 font-semibold uppercase">Success Rate</p>
                  <h4 className="text-2xl font-black text-slate-100">{Math.round(parsing.success_rate * 100)}%</h4>
                </div>
                <Database className="text-indigo-400" size={28} />
              </div>
            </div>
          ) : (
            <p className="text-slate-500 text-sm text-center py-4">No parsing data available.</p>
          )}
        </Card>

        {/* Sourcing channels */}
        <Card title="Sourcing Channel Conversion" className="lg:col-span-2">
          {sources.length === 0 ? (
            <p className="text-slate-500 text-sm text-center py-10">No candidate source information recorded.</p>
          ) : (
            <Table>
              <Thead>
                <Tr>
                  <Th>Source Channel</Th>
                  <Th>Registered Profiles</Th>
                  <Th>Shortlisted</Th>
                  <Th className="text-right">Conversion Rate</Th>
                </Tr>
              </Thead>
              <Tbody>
                {sources.map((item) => (
                  <Tr key={item.source}>
                    <Td className="font-semibold text-slate-200">{item.source}</Td>
                    <Td>{item.count}</Td>
                    <Td>{item.shortlisted_count}</Td>
                    <Td className="text-right font-bold text-indigo-400">
                      {Math.round(item.shortlist_rate * 100)}%
                    </Td>
                  </Tr>
                ))}
              </Tbody>
            </Table>
          )}
        </Card>
      </div>

      {/* Recruitment event audit logs */}
      <Card title="Recruitment Events Logs (Audit Trail)">
        {events.length === 0 ? (
          <p className="text-slate-500 text-sm text-center py-6">No security or activity events logged.</p>
        ) : (
          <div className="overflow-x-auto">
            <Table>
              <Thead>
                <Tr>
                  <Th>Timestamp</Th>
                  <Th>Event Log</Th>
                  <Th>Description / Payload Details</Th>
                  <Th>Actor ID</Th>
                </Tr>
              </Thead>
              <Tbody>
                {events.map((ev) => (
                  <Tr key={ev.id}>
                    <Td className="text-xs text-slate-500 whitespace-nowrap">
                      {new Date(ev.created_at).toLocaleString()}
                    </Td>
                    <Td className="font-semibold text-xs text-indigo-305 whitespace-nowrap">
                      {ev.event_type}
                    </Td>
                    <Td className="text-xs text-slate-300 max-w-[300px] truncate">
                      {ev.details?.description || ev.details?.message || JSON.stringify(ev.details) || 'Activity registered.'}
                    </Td>
                    <Td className="text-xs text-slate-500 truncate max-w-[120px]">
                      {ev.actor_id || 'System'}
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
