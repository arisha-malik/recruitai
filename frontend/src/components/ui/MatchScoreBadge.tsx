import React from 'react';

interface MatchScoreBadgeProps {
  score: number;
  size?: 'sm' | 'md' | 'lg';
}

export const MatchScoreBadge: React.FC<MatchScoreBadgeProps> = ({ score, size = 'md' }) => {
  const getColors = (val: number) => {
    if (val >= 80) {
      return {
        bg: 'bg-emerald-500/10',
        text: 'text-emerald-400',
        border: 'border-emerald-500/35',
      };
    }
    if (val >= 50) {
      return {
        bg: 'bg-amber-500/10',
        text: 'text-amber-400',
        border: 'border-amber-500/35',
      };
    }
    return {
      bg: 'bg-rose-500/10',
      text: 'text-rose-400',
      border: 'border-rose-500/35',
    };
  };

  const getSizeStyles = (sz: 'sm' | 'md' | 'lg') => {
    switch (sz) {
      case 'sm':
        return 'text-xs px-1.5 py-0.5 font-bold';
      case 'lg':
        return 'text-lg px-4 py-2 font-black';
      default:
        return 'text-sm px-2.5 py-1 font-extrabold';
    }
  };

  const colors = getColors(score);

  return (
    <span
      className={`inline-flex items-center rounded-lg border shadow-sm ${colors.bg} ${colors.text} ${colors.border} ${getSizeStyles(
        size
      )}`}
    >
      {score}% Match
    </span>
  );
};
