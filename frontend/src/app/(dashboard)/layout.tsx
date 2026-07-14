"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import SettingsModal from "@/components/SettingsModal";
import ProfileModal from "@/components/ProfileModal";
import { 
  Sparkles, 
  LayoutDashboard, 
  Users, 
  Briefcase, 
  Settings, 
  LogOut, 
  Menu, 
  X, 
  Search,
  UploadCloud,
  FileText,
  HelpCircle,
  BarChart3,
  CalendarClock
} from "lucide-react";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState<{ email: string; role: string } | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isProfileOpen, setIsProfileOpen] = useState(false);
  const pathname = usePathname();
  const router = useRouter();

  useEffect(() => {
    if (typeof window !== "undefined") {
      const token = localStorage.getItem("token");
      if (!token) {
        setIsAuthenticated(false);
        router.push("/login");
      } else {
        setIsAuthenticated(true);
        const storedUser = localStorage.getItem("user");
        if (storedUser) {
          try {
            setUser(JSON.parse(storedUser));
          } catch (e) {
            console.error("Failed to parse stored user", e);
          }
        }
      }
      setLoading(false);
    }
  }, [router]);

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    router.push("/login");
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      router.push(`/search?q=${encodeURIComponent(searchQuery.trim())}`);
    }
  };

  const navigation = [
    { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
    { name: "Candidates", href: "/candidates", icon: Users },
    { name: "Upload Resume", href: "/resumes/upload", icon: UploadCloud },
    { name: "Jobs", href: "/jobs", icon: Briefcase },
    { name: "Interview Round", href: "/interviews", icon: CalendarClock },
    { name: "JD Generator", href: "/assistant/generate-jd", icon: FileText },
    { name: "Interview Assistant", href: "/assistant/interview-questions", icon: HelpCircle },
    { name: "Analytics", href: "/analytics", icon: BarChart3 },
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-[#f7faf5]">
        <div className="flex flex-col items-center">
          <div className="w-10 h-10 border-4 border-[#caead6] border-t-[#476353] rounded-full animate-spin"></div>
          <p className="mt-4 text-sm font-semibold text-[#424844] animate-pulse">Authorizing session...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  const emailDisplay = user ? user.email : "recruiter@company.com";
  const nameDisplay = user ? user.email.split("@")[0] : "Recruiter";
  const roleDisplay = user ? user.role : "Recruitment Lead";
  const initialsDisplay = user ? user.email.substring(0, 2).toUpperCase() : "RC";

  return (
    <div className="min-h-screen bg-[#f7faf5] text-[#191c1a] font-sans flex flex-col md:flex-row antialiased selection:bg-[#caead6] selection:text-[#314d3e]">
      
      {/* Mobile Top Navigation */}
      <header className="md:hidden bg-white border-b border-[#e6e9e4] px-6 py-4 flex items-center justify-between sticky top-0 z-40">
        <span className="text-xl font-black text-[#476353]">RecruitAI</span>
        <div className="flex items-center gap-3">
          <button 
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-2 text-[#424844] hover:bg-[#f1f4f0] rounded-lg transition-all"
          >
            {sidebarOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>
      </header>

      {/* Sidebar Navigation */}
      <aside className={`
        fixed inset-y-0 left-0 z-50 w-72 bg-[#f1f4f0] border-r border-[#e6e9e4] px-6 py-8 flex flex-col justify-between 
        transform transition-transform duration-300 md:relative md:transform-none
        ${sidebarOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"}
      `}>
        <div className="space-y-8">
          {/* Logo */}
          <div className="flex items-center justify-between">
            <Link href="/" className="flex items-center gap-2">
              <span className="text-2xl font-black tracking-tight text-[#476353]">RecruitAI</span>
            </Link>
            <button 
              onClick={() => setSidebarOpen(false)}
              className="md:hidden p-1.5 text-[#424844] hover:bg-[#e6e9e4] rounded-lg"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* AI Status Badge */}
          <div className="p-4 bg-[#caead6]/60 rounded-2xl border border-[#caead6] space-y-2">
            <div className="flex items-center gap-2 text-xs font-bold text-[#314d3e] uppercase tracking-wide">
              <Sparkles className="w-4 h-4 text-[#476353] animate-pulse" />
              Intelligence Online
            </div>
            <p className="text-[11px] text-[#424844] leading-relaxed">
              RecruitAI is actively analyzing candidate profiles and tracking hiring workflows.
            </p>
          </div>

          {/* Navigation Links */}
          <nav className="space-y-1.5 overflow-y-auto max-h-[50vh]">
            <div className="text-[10px] font-bold text-[#727973] uppercase tracking-wider px-3 mb-2">
              Hiring Desk
            </div>
            {navigation.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href || (item.href !== "/dashboard" && pathname.startsWith(item.href + "/"));
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  onClick={() => setSidebarOpen(false)}
                  className={`
                    flex items-center gap-3.5 px-4.5 py-3 rounded-xl text-sm font-semibold transition-all group
                    ${isActive 
                      ? "bg-white text-[#476353] shadow-sm shadow-[#476353]/5 border-l-4 border-[#476353]" 
                      : "text-[#424844] hover:bg-white/50 hover:text-[#476353]"}
                  `}
                >
                  <Icon className={`w-5 h-5 transition-transform group-hover:scale-105 ${isActive ? "text-[#476353]" : "text-[#727973]"}`} />
                  {item.name}
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Sidebar Footer */}
        <div className="space-y-4 pt-6 border-t border-[#e6e9e4]">
          <button
            onClick={() => setIsSettingsOpen(true)}
            className="w-full flex items-center gap-3.5 px-4.5 py-2.5 rounded-xl text-sm font-semibold text-[#424844] hover:bg-white/50 hover:text-[#476353] transition-all text-left"
          >
            <Settings className="w-5 h-5 text-[#727973]" />
            Settings
          </button>
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-3.5 px-4.5 py-2.5 rounded-xl text-sm font-semibold text-[#994236] hover:bg-[#ffdad4]/40 transition-all text-left"
          >
            <LogOut className="w-5 h-5 text-[#994236]" />
            Sign Out
          </button>

          {/* User Profile */}
          <div className="flex items-center gap-3 p-2 bg-white/40 rounded-2xl border border-[#f0eae4] mt-2">
            <div className="w-10 h-10 rounded-full bg-[#5f7c6b] text-white flex items-center justify-center text-sm font-bold shadow-sm">
              {initialsDisplay}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-bold text-[#191c1a] truncate capitalize">{nameDisplay}</p>
              <p className="text-[10px] text-[#727973] truncate capitalize">{roleDisplay}</p>
            </div>
          </div>
        </div>

      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        {/* Desktop Topbar */}
        <header className="hidden md:flex bg-white/40 backdrop-blur-md border-b border-[#e6e9e4]/60 px-10 py-5 items-center justify-between sticky top-0 z-10">
          <form onSubmit={handleSearch} className="relative w-80">
            <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-[#727973]">
              <Search className="w-4 h-4" />
            </span>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search candidates by skills, role, location..."
              className="w-full pl-9 pr-4 py-2.5 bg-white/70 border border-[#e6e9e4] rounded-xl text-xs placeholder-[#727973] focus:outline-none focus:ring-1 focus:ring-[#476353] focus:border-transparent transition-all"
            />
          </form>
          <div className="flex items-center gap-5">
            <button onClick={() => setIsProfileOpen(true)} className="flex items-center gap-3 hover:bg-white border border-transparent hover:border-[#e6e9e4] p-1.5 rounded-2xl transition-all text-left">
              <div className="text-right hidden sm:block">
                <p className="text-xs font-bold text-[#191c1a] capitalize">{nameDisplay}</p>
                <p className="text-[10px] text-[#727973] capitalize">{roleDisplay}</p>
              </div>
              <div className="w-9 h-9 rounded-full bg-[#5f7c6b] text-white flex items-center justify-center text-xs font-bold shadow-sm">
                {initialsDisplay}
              </div>
            </button>
          </div>
        </header>

        {/* Dynamic page content */}
        <div className="p-6 md:p-10 flex-1">
          {children}
        </div>
      </main>

      <SettingsModal isOpen={isSettingsOpen} onClose={() => setIsSettingsOpen(false)} />
      <ProfileModal isOpen={isProfileOpen} onClose={() => setIsProfileOpen(false)} user={user} onLogout={handleLogout} />
    </div>
  );
}
