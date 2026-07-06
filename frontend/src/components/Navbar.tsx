'use client';

import React, { useEffect, useState } from 'react';
import { Menu, User, ShieldAlert } from 'lucide-react';

interface NavbarProps {
  onMenuClick: () => void;
}

export default function Navbar({ onMenuClick }: NavbarProps) {
  const [user, setUser] = useState<{ email: string; role: string } | null>(null);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const storedUser = localStorage.getItem('user');
      if (storedUser) {
        try {
          setUser(JSON.parse(storedUser));
        } catch (e) {
          console.error(e);
        }
      }
    }
  }, []);

  return (
    <header className="h-16 bg-[#161e31] border-b border-[#223049] flex items-center justify-between px-6 z-20 relative">
      {/* Mobile Menu Trigger */}
      <div className="flex items-center gap-4">
        <button
          onClick={onMenuClick}
          className="lg:hidden p-2 -ml-2 rounded-lg text-slate-400 hover:bg-slate-800/40 hover:text-slate-200"
        >
          <Menu size={20} />
        </button>
        <h2 className="text-lg font-bold text-slate-100 hidden sm:block">Talent Assistant Panel</h2>
      </div>

      {/* User Actions */}
      <div className="flex items-center gap-4">
        {user && (
          <div className="flex items-center gap-3">
            {/* User Details */}
            <div className="text-right hidden md:block">
              <p className="text-sm font-semibold text-slate-200">{user.email}</p>
              <span className="text-[10px] uppercase font-bold tracking-wider text-indigo-400 bg-indigo-500/10 border border-indigo-500/20 px-2 py-0.5 rounded-full">
                {user.role}
              </span>
            </div>

            {/* Avatar Placeholder */}
            <div className="w-9 h-9 rounded-full bg-slate-800 flex items-center justify-center border border-[#223049] text-indigo-400">
              <User size={18} />
            </div>
          </div>
        )}
      </div>
    </header>
  );
}
