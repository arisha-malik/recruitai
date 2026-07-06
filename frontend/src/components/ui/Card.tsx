import React from 'react';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  title?: string;
  subtitle?: string;
}

export const Card: React.FC<CardProps> = ({ title, subtitle, children, className = '', ...props }) => {
  return (
    <div
      className={`bg-card border border-border rounded-xl p-6 shadow-lg transition-all duration-300 hover:border-indigo-500/30 ${className}`}
      {...props}
    >
      {title && (
        <div className="mb-4">
          <h3 className="text-lg font-semibold text-slate-900">{title}</h3>
          {subtitle && <p className="text-sm text-slate-400 mt-1">{subtitle}</p>}
        </div>
      )}
      {children}
    </div>
  );
};
