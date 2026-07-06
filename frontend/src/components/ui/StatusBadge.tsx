import React from 'react';

interface StatusBadgeProps {
  status: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status }) => {
  const getBadgeStyles = (val: string) => {
    const s = val.toUpperCase();
    switch (s) {
      // Job Statuses
      case 'OPEN':
      case 'ACTIVE':
        return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20';
      case 'DRAFT':
        return 'bg-slate-500/10 text-slate-400 border-slate-500/20';
      case 'CLOSED':
        return 'bg-rose-500/10 text-rose-400 border-rose-500/20';

      // Resume Parsing Statuses
      case 'UPLOADED':
        return 'bg-blue-500/10 text-blue-400 border-blue-500/20';
      case 'PARSING':
        return 'bg-amber-500/10 text-amber-400 border-amber-500/20 animate-pulse';
      case 'PARSED':
        return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20';
      case 'FAILED':
        return 'bg-rose-500/10 text-rose-400 border-rose-500/20';

      // Application Statuses
      case 'APPLIED':
        return 'bg-blue-500/10 text-blue-400 border-blue-500/20';
      case 'MATCHED':
        return 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20';
      case 'SHORTLISTED':
      case 'SHORTLIST':
        return 'bg-teal-500/10 text-teal-400 border-teal-500/20';
      case 'INTERVIEWING':
        return 'bg-violet-500/10 text-violet-400 border-violet-500/20';
      case 'OFFERED':
        return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20';
      case 'REJECTED':
      case 'REJECT':
        return 'bg-rose-500/10 text-rose-400 border-rose-500/20';
      case 'MAYBE':
        return 'bg-amber-500/10 text-amber-400 border-amber-500/20';

      default:
        return 'bg-slate-500/10 text-slate-300 border-slate-500/20';
    }
  };

  return (
    <span
      className={`inline-flex items-center text-xs font-semibold px-2.5 py-1 rounded-full border ${getBadgeStyles(
        status
      )}`}
    >
      {status}
    </span>
  );
};
