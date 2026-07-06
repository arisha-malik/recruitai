'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { 
  LayoutDashboard, 
  Users, 
  UploadCloud, 
  Briefcase, 
  FileText, 
  HelpCircle, 
  BarChart3, 
  LogOut 
} from 'lucide-react';

interface SidebarProps {
  onClose?: () => void;
}

export default function Sidebar({ onClose }: SidebarProps) {
  const pathname = usePathname();
  const router = useRouter();

  const navItems = [
    { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
    { name: 'Jobs', href: '/jobs', icon: Briefcase },
    { name: 'Candidates', href: '/candidates', icon: Users },
    { name: 'Interview Round', href: '/interviews', icon: HelpCircle },
    { name: 'Upload Resume', href: '/resumes/upload', icon: UploadCloud },
    { name: 'JD Generator', href: '/assistant/generate-jd', icon: FileText },
    { name: 'Interview Assistant', href: '/assistant/interview-questions', icon: HelpCircle },
    { name: 'Analytics', href: '/analytics', icon: BarChart3 },
  ];

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    router.push('/login');
    if (onClose) onClose();
  };

  return (
    <aside className="w-64 bg-[#161e31] border-r border-[#223049] h-full flex flex-col justify-between">
      {/* Brand logo / header */}
      <div>
        <div className="h-16 flex items-center px-6 border-b border-[#223049]">
          <Link 
            href="/dashboard" 
            className="text-xl font-black bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent"
            onClick={onClose}
          >
            RecruitAI
          </Link>
        </div>

        {/* Navigation list */}
        <nav className="p-4 space-y-1.5">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href || pathname.startsWith(item.href + '/');
            return (
              <Link
                key={item.name}
                href={item.href}
                onClick={onClose}
                className={`flex items-center gap-3.5 px-4 py-3 rounded-lg text-sm font-medium transition-all duration-150 ${
                  isActive 
                    ? 'bg-gradient-to-r from-indigo-500/20 to-purple-500/10 border border-indigo-500/35 text-indigo-300' 
                    : 'text-slate-400 hover:bg-slate-800/40 hover:text-slate-200 border border-transparent'
                }`}
              >
                <Icon size={18} className={isActive ? 'text-indigo-400' : 'text-slate-400'} />
                {item.name}
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Logout section */}
      <div className="p-4 border-t border-[#223049]">
        <button
          onClick={handleLogout}
          className="flex items-center gap-3.5 w-full px-4 py-3 rounded-lg text-sm font-medium text-rose-400 hover:bg-rose-500/10 transition-all duration-150 border border-transparent active:scale-[0.98]"
        >
          <LogOut size={18} />
          Sign Out
        </button>
      </div>
    </aside>
  );
}
