import React from 'react';
import { X, User, Mail, Shield, LogOut } from 'lucide-react';

interface ProfileModalProps {
  isOpen: boolean;
  onClose: () => void;
  user: { email: string; role: string } | null;
  onLogout: () => void;
}

export default function ProfileModal({ isOpen, onClose, user, onLogout }: ProfileModalProps) {
  if (!isOpen || !user) return null;

  const nameDisplay = user.email.split("@")[0];
  const initialsDisplay = user.email.substring(0, 2).toUpperCase();

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
      <div className="w-full max-w-sm bg-white rounded-2xl shadow-2xl relative overflow-hidden flex flex-col animate-fadeIn">
        <div className="flex justify-between items-center p-5 border-b border-[#e6e9e4] bg-[#f7faf5]">
          <h3 className="text-lg font-bold text-[#191c1a]">User Profile</h3>
          <button onClick={onClose} className="text-[#727973] hover:text-[#191c1a] transition-colors">
            <X size={20} />
          </button>
        </div>

        <div className="p-6 flex flex-col items-center border-b border-[#e6e9e4]">
          <div className="w-20 h-20 rounded-full bg-gradient-to-br from-[#476353] to-[#314d3e] text-white flex items-center justify-center text-3xl font-black shadow-lg mb-4">
            {initialsDisplay}
          </div>
          <h2 className="text-xl font-bold text-[#191c1a] capitalize">{nameDisplay}</h2>
          <span className="text-xs bg-[#caead6] text-[#314d3e] px-3 py-1 rounded-full font-bold uppercase tracking-wider mt-2 border border-[#476353]/20">
            {user.role}
          </span>
        </div>

        <div className="p-6 space-y-4">
          <div className="flex items-center gap-3 p-3 bg-[#f1f4f0] rounded-xl border border-[#e6e9e4]">
            <User size={18} className="text-[#727973]" />
            <div>
              <p className="text-[10px] uppercase font-bold text-[#727973] tracking-wider">Full Name</p>
              <p className="text-sm font-semibold text-[#191c1a] capitalize">{nameDisplay}</p>
            </div>
          </div>

          <div className="flex items-center gap-3 p-3 bg-[#f1f4f0] rounded-xl border border-[#e6e9e4]">
            <Mail size={18} className="text-[#727973]" />
            <div>
              <p className="text-[10px] uppercase font-bold text-[#727973] tracking-wider">Email Address</p>
              <p className="text-sm font-semibold text-[#191c1a]">{user.email}</p>
            </div>
          </div>

          <div className="flex items-center gap-3 p-3 bg-[#f1f4f0] rounded-xl border border-[#e6e9e4]">
            <Shield size={18} className="text-[#727973]" />
            <div>
              <p className="text-[10px] uppercase font-bold text-[#727973] tracking-wider">Account Role</p>
              <p className="text-sm font-semibold text-[#191c1a] capitalize">{user.role.toLowerCase()}</p>
            </div>
          </div>
        </div>

        <div className="p-4 bg-[#f7faf5] border-t border-[#e6e9e4]">
          <button
            onClick={() => {
              onLogout();
              onClose();
            }}
            className="w-full flex justify-center items-center gap-2 px-5 py-2.5 bg-rose-50 hover:bg-rose-100 text-rose-600 border border-rose-200 text-sm font-bold rounded-lg transition-colors"
          >
            <LogOut size={16} />
            Sign Out
          </button>
        </div>
      </div>
    </div>
  );
}
