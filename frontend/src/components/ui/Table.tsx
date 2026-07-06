import React from 'react';

interface TableProps extends React.TableHTMLAttributes<HTMLTableElement> {}

export const Table: React.FC<TableProps> = ({ children, className = '', ...props }) => {
  return (
    <div className="w-full overflow-x-auto rounded-lg border border-border">
      <table className={`w-full text-left border-collapse ${className}`} {...props}>
        {children}
      </table>
    </div>
  );
};

export const Thead: React.FC<React.HTMLAttributes<HTMLTableSectionElement>> = ({ children, className = '', ...props }) => {
  return (
    <thead className={`bg-slate-900/60 border-b border-border text-xs uppercase tracking-wider text-slate-300 font-medium ${className}`} {...props}>
      {children}
    </thead>
  );
};

export const Tbody: React.FC<React.HTMLAttributes<HTMLTableSectionElement>> = ({ children, className = '', ...props }) => {
  return <tbody className={`divide-y divide-border/60 ${className}`} {...props}>{children}</tbody>;
};

export const Tr: React.FC<React.HTMLAttributes<HTMLTableRowElement>> = ({ children, className = '', ...props }) => {
  return (
    <tr className={`hover:bg-slate-800/40 transition-colors duration-150 ${className}`} {...props}>
      {children}
    </tr>
  );
};

export const Th: React.FC<React.ThHTMLAttributes<HTMLTableCellElement>> = ({ children, className = '', ...props }) => {
  return <th className={`p-4 text-slate-300 font-semibold ${className}`} {...props}>{children}</th>;
};

export const Td: React.FC<React.TdHTMLAttributes<HTMLTableCellElement>> = ({ children, className = '', ...props }) => {
  return <td className={`p-4 text-slate-300 text-sm align-middle ${className}`} {...props}>{children}</td>;
};
