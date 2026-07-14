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
