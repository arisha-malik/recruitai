"use client";

import React from "react";
import Link from "next/link";
import { Sparkles, ArrowRight, ChevronRight, Bell, FileText, UserCheck, BarChart2, MessageSquare } from "lucide-react";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-[#f7faf5] text-[#191c1a] font-sans antialiased selection:bg-[#caead6] selection:text-[#314d3e]">
      {/* Top Header */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-[#f7faf5]/80 backdrop-blur-md border-b border-[#e6e9e4]/40 px-6 py-4 md:px-12 flex justify-between items-center transition-all duration-300">
        <div className="flex items-center gap-3">
          <span className="text-2xl font-black tracking-tight text-[#476353]">RecruitAI</span>
        </div>
        <nav className="hidden md:flex items-center gap-10">
          <Link href="/dashboard" className="text-[#476353] font-semibold text-sm relative after:absolute after:-bottom-2 after:left-1/2 after:-translate-x-1/2 after:w-1 after:h-1 after:bg-[#476353] after:rounded-full">
            Dashboard
          </Link>
          <Link href="/dashboard" className="text-[#424844] font-medium text-sm hover:text-[#476353] transition-colors">
            Candidates
          </Link>
          <Link href="/dashboard" className="text-[#424844] font-medium text-sm hover:text-[#476353] transition-colors">
            Jobs
          </Link>
          <Link href="/dashboard" className="text-[#424844] font-medium text-sm hover:text-[#476353] transition-colors">
            AI Assistant
          </Link>
        </nav>
        <div className="flex items-center gap-4">
          <button className="p-2 text-[#424844] hover:bg-[#e6e9e4] rounded-full transition-all">
            <Bell className="w-5 h-5" />
          </button>
          <Link href="/login">
            <div className="w-10 h-10 rounded-full bg-[#e6e2dc] flex items-center justify-center overflow-hidden border-2 border-white shadow-sm cursor-pointer">
              <div className="w-full h-full bg-[#5f7c6b] text-white flex items-center justify-center text-sm font-semibold">
                AM
              </div>
            </div>
          </Link>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative min-h-screen pt-32 pb-16 px-6 md:px-12 flex flex-col justify-center items-center bg-gradient-to-tr from-[#caead6]/20 via-[#f7faf5] to-[#f7faf5]">
        <div className="max-w-7xl w-full grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">

          {/* Left Hero Content */}
          <div className="space-y-8 animate-fade-in">
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-[#caead6] text-[#314d3e] font-semibold text-xs tracking-wide">
              <Sparkles className="w-4 h-4 text-[#476353]" />
              Next-Gen Hiring Workspace
            </div>

            <h1 className="text-4xl md:text-5xl lg:text-6xl font-extrabold tracking-tight text-[#191c1a] leading-[1.1] max-w-xl">
              AI-powered hiring intelligence for modern recruitment teams
            </h1>

            <p className="text-lg md:text-xl text-[#424844] font-normal leading-relaxed max-w-lg">
              Transform your messy pipeline into a streamlined, high-quality talent machine. RecruitAI understands context, skills, and career trajectory like a human partner.
            </p>

            <div className="flex flex-wrap gap-4 pt-2">
              <Link href="/login" className="px-8 py-4 bg-[#476353] text-white rounded-2xl font-semibold text-sm shadow-lg shadow-[#476353]/10 hover:shadow-xl hover:translate-y-[-2px] transition-all duration-300 flex items-center gap-2">
                Enter Dashboard
                <ArrowRight className="w-4 h-4" />
              </Link>
              <Link href="/dashboard" className="px-8 py-4 border border-[#476353] text-[#476353] bg-transparent rounded-2xl font-semibold text-sm hover:bg-[#476353]/5 transition-all duration-300">
                View Demo Dashboard
              </Link>
            </div>

            {/* Trusted by agency section */}
            <div className="flex items-center gap-4 pt-4 border-t border-[#e6e9e4]/60">
              <div className="flex -space-x-3">
                <div className="w-8 h-8 rounded-full border-2 border-white bg-[#5f7c6b] text-white flex items-center justify-center text-[10px] font-bold">JD</div>
                <div className="w-8 h-8 rounded-full border-2 border-white bg-[#994236] text-white flex items-center justify-center text-[10px] font-bold">SK</div>
                <div className="w-8 h-8 rounded-full border-2 border-white bg-[#e6e2dc] text-[#1c1c18] flex items-center justify-center text-[10px] font-bold">LW</div>
              </div>
              <p className="text-sm font-medium text-[#424844]">Trusted by 500+ recruitment agencies</p>
            </div>
          </div>

          {/* Right Hero Visual (Rendered beautifully with CSS gradients and animation effects) */}
          <div className="relative flex justify-center lg:justify-end">
            <div className="relative z-10 bg-white/40 backdrop-blur-md p-4 rounded-[32px] border border-[#f0eae4] shadow-2xl shadow-[#5f7c6b]/5 overflow-hidden aspect-square w-full max-w-[500px]">
              <div className="relative w-full h-full bg-[#ecefea] rounded-2xl overflow-hidden flex items-center justify-center min-h-[350px]">
                {/* Simulated 3D ambient design element */}
                <div className="absolute w-72 h-72 rounded-full bg-[#caead6]/60 blur-3xl -top-12 -right-12"></div>
                <div className="absolute w-64 h-64 rounded-full bg-[#ffdad4]/40 blur-3xl -bottom-12 -left-12"></div>

                {/* 3D Shapes rendered cleanly via Tailwind and animations */}
                <div className="relative z-10 flex flex-col items-center justify-center text-center p-8">
                  <div className="relative w-48 h-48 rounded-full bg-gradient-to-br from-[#caead6] to-[#5f7c6b] flex items-center justify-center shadow-inner animate-pulse">
                    <div className="absolute w-36 h-36 rounded-full bg-white/10 backdrop-blur-md border border-white/20 animate-spin" style={{ animationDuration: "20s" }}></div>
                    <Sparkles className="w-16 h-16 text-white" />
                  </div>
                  <div className="mt-6 space-y-1">
                    <div className="text-xs font-bold uppercase tracking-widest text-[#314d3e]">RecruitAI Intelligence</div>
                    <div className="text-lg font-bold text-[#191c1a]">Analyzing 12,450+ Candidates</div>
                  </div>
                </div>
              </div>
            </div>

            {/* Ambient Background glows */}
            <div className="absolute -top-10 -right-10 w-40 h-40 bg-[#ffdad4]/30 rounded-full blur-3xl -z-10"></div>
            <div className="absolute -bottom-10 -left-10 w-64 h-64 bg-[#caead6]/40 rounded-full blur-[80px] -z-10"></div>
          </div>

        </div>
      </section>

      {/* Value Proposition Section */}
      <section className="py-24 px-6 md:px-12 bg-white">
        <div className="max-w-7xl mx-auto">
          <div className="text-center space-y-4 mb-20">
            <h2 className="text-3xl md:text-4xl font-bold text-[#191c1a] tracking-tight">Designed for clarity and focus</h2>
            <p className="text-base md:text-lg text-[#424844] max-w-2xl mx-auto">
              We've replaced complex spreadsheets with intelligent interfaces that let you focus on what matters: the human connection.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {/* Bento Card 1: Resume Parsing */}
            <div className="lg:col-span-2 bg-[#f7faf5]/40 backdrop-blur-md p-8 md:p-10 rounded-3xl border border-[#f0eae4] flex flex-col md:flex-row gap-8 items-center hover:translate-y-[-4px] hover:shadow-lg transition-all duration-300 cursor-default">
              <div className="flex-1 space-y-6">
                <div className="w-12 h-12 rounded-2xl bg-[#caead6] flex items-center justify-center text-[#476353]">
                  <FileText className="w-6 h-6" />
                </div>
                <h3 className="text-2xl font-bold text-[#191c1a]">Semantic Resume Parsing</h3>
                <p className="text-sm md:text-base text-[#424844] leading-relaxed">
                  Our AI doesn't just look for keywords; it understands the trajectory of a career. It identifies transferable skills and growth potential that simple filters miss.
                </p>
                <div className="pt-2">
                  <Link href="/dashboard" className="text-[#476353] font-semibold text-sm flex items-center gap-1 group">
                    Explore Technology
                    <ChevronRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                  </Link>
                </div>
              </div>
              <div className="flex-1 w-full bg-[#f1f4f0] rounded-2xl p-6 shadow-sm border border-[#e6e9e4]/60">
                <div className="space-y-4">
                  <div className="bg-white p-3.5 rounded-xl flex items-center justify-between shadow-sm">
                    <div className="flex items-center gap-3">
                      <div className="w-2.5 h-2.5 rounded-full bg-[#caead6]"></div>
                      <div className="space-y-1">
                        <div className="h-3 w-28 bg-[#ecefea] rounded"></div>
                        <div className="h-2 w-16 bg-[#e6e9e4] rounded"></div>
                      </div>
                    </div>
                    <span className="text-xs font-bold text-[#476353] bg-[#caead6]/30 px-2.5 py-1 rounded-full">Senior Engineer</span>
                  </div>
                  <div className="bg-white p-3.5 rounded-xl flex items-center justify-between shadow-sm ml-6 border-l-2 border-[#994236]">
                    <div className="flex items-center gap-3">
                      <div className="w-2.5 h-2.5 rounded-full bg-[#ffdad4]"></div>
                      <div className="space-y-1">
                        <div className="h-3 w-24 bg-[#ecefea] rounded"></div>
                        <div className="h-2 w-14 bg-[#e6e9e4] rounded"></div>
                      </div>
                    </div>
                    <span className="text-xs font-bold text-[#994236] bg-[#ffdad4]/40 px-2.5 py-1 rounded-full">Product Lead</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Bento Card 2: Intelligent Matching */}
            <div className="bg-[#f7faf5]/40 backdrop-blur-md p-8 rounded-3xl border border-[#f0eae4] flex flex-col justify-between hover:translate-y-[-4px] hover:shadow-lg transition-all duration-300">
              <div className="space-y-6">
                <div className="w-12 h-12 rounded-2xl bg-[#ffdad4] flex items-center justify-center text-[#994236]">
                  <UserCheck className="w-6 h-6" />
                </div>
                <h3 className="text-2xl font-bold text-[#191c1a]">Intelligent Matching</h3>
                <p className="text-sm md:text-base text-[#424844] leading-relaxed">
                  Context-aware ranking that pairs the right personality with the right team culture, instantly.
                </p>
              </div>
              <div className="pt-6 border-t border-[#e6e9e4] flex justify-between items-center mt-6">
                <span className="text-xs font-bold text-[#994236] tracking-wider uppercase">98% Accuracy Rate</span>
                <div className="flex gap-1">
                  <div className="w-2.5 h-2.5 rounded-full bg-[#994236] animate-pulse"></div>
                  <div className="w-2.5 h-2.5 rounded-full bg-[#994236]/30"></div>
                </div>
              </div>
            </div>

            {/* Bento Card 3: Hiring Flow */}
            <div className="bg-[#f7faf5]/40 backdrop-blur-md p-8 rounded-3xl border border-[#f0eae4] space-y-6 hover:translate-y-[-4px] hover:shadow-lg transition-all duration-300">
              <div className="w-12 h-12 rounded-2xl bg-[#e6e2dc] flex items-center justify-center text-[#605e5a]">
                <BarChart2 className="w-6 h-6" />
              </div>
              <h3 className="text-2xl font-bold text-[#191c1a]">Hiring Flow</h3>
              <p className="text-sm md:text-base text-[#424844] leading-relaxed">
                Visualize your entire pipeline with elegant, heat-mapped flow charts that highlight process bottlenecks.
              </p>
            </div>

            {/* Bento Card 4: Collaborative Workspaces */}
            <div className="lg:col-span-2 bg-[#f7faf5]/40 backdrop-blur-md p-8 md:p-10 rounded-3xl border border-[#f0eae4] flex flex-col md:flex-row-reverse gap-8 items-center hover:translate-y-[-4px] hover:shadow-lg transition-all duration-300">
              <div className="flex-1 space-y-6">
                <div className="w-12 h-12 rounded-2xl bg-[#caead6] flex items-center justify-center text-[#476353]">
                  <MessageSquare className="w-6 h-6" />
                </div>
                <h3 className="text-2xl font-bold text-[#191c1a]">Collaborative Workspaces</h3>
                <p className="text-sm md:text-base text-[#424844] leading-relaxed">
                  Share candidate shortlists with hiring managers in one click. Gather feedback and consensus without ever leaving the platform.
                </p>
              </div>
              <div className="flex-1 w-full flex items-center justify-center py-4">
                <div className="relative w-full max-w-[280px]">
                  <div className="bg-white p-5 rounded-2xl shadow-md -rotate-2 border border-[#f0eae4]">
                    <div className="flex items-center gap-3 mb-3">
                      <div className="w-8 h-8 rounded-full bg-[#caead6] text-[#314d3e] flex items-center justify-center text-xs font-bold">HM</div>
                      <div className="space-y-1">
                        <div className="h-2.5 w-20 bg-[#ecefea] rounded"></div>
                        <div className="h-1.5 w-12 bg-[#e6e9e4] rounded"></div>
                      </div>
                    </div>
                    <div className="h-2 w-full bg-[#f1f4f0] rounded mb-1.5"></div>
                    <div className="h-2 w-5/6 bg-[#f1f4f0] rounded"></div>
                  </div>
                  <div className="absolute -top-4 -right-4 bg-[#476353] text-white px-4 py-2 rounded-full text-xs font-bold rotate-3 shadow-lg">
                    "Perfect match for the role!"
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* AI Search Teaser Call to Action */}
      <section className="py-20 px-6 md:px-12 bg-[#f7faf5]">
        <div className="max-w-5xl mx-auto bg-[#5f7c6b] text-white rounded-[32px] p-8 md:p-14 relative overflow-hidden shadow-xl shadow-[#476353]/10">
          <div className="relative z-10 grid grid-cols-1 md:grid-cols-2 gap-8 items-center">
            <div className="space-y-6">
              <h2 className="text-3xl md:text-4xl font-bold text-white tracking-tight">Ready to hire smarter?</h2>
              <p className="text-base text-[#fcfffa]/90 leading-relaxed max-w-md">
                Join thousands of recruiters who have reclaimed their time and found better candidates with RecruitAI.
              </p>
              <div className="pt-2">
                <Link href="/login" className="px-8 py-4 bg-white text-[#476353] font-bold text-sm rounded-xl hover:bg-[#f7faf5] transition-all inline-block shadow-md">
                  Start Free Trial
                </Link>
              </div>
            </div>

            <div className="flex flex-col gap-4">
              <div className="p-6 bg-white/10 backdrop-blur-md rounded-2xl border border-white/20 shadow-inner">
                <p className="text-sm md:text-base font-semibold mb-3 italic text-white">
                  "Find me a Senior React Dev with FinTech experience who speaks French."
                </p>
                <div className="flex items-center gap-2.5 text-[#caead6]">
                  <Sparkles className="w-5 h-5 animate-pulse" />
                  <span className="text-xs font-bold tracking-wider uppercase">AI Assistant is searching...</span>
                </div>
              </div>
            </div>
          </div>

          {/* Decorative radial glows */}
          <div className="absolute -right-24 -bottom-24 w-96 h-96 bg-[#caead6]/20 rounded-full blur-3xl"></div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-16 px-6 md:px-12 border-t border-[#e6e9e4] bg-[#f1f4f0]">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-start gap-12">
          <div className="space-y-4 max-w-xs">
            <span className="text-2xl font-black text-[#476353]">RecruitAI</span>
            <p className="text-sm text-[#424844] leading-relaxed">
              The human-first intelligence platform for modern recruitment teams.
            </p>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-3 gap-10">
            <div className="space-y-4">
              <h4 className="text-sm font-bold text-[#191c1a] tracking-wide uppercase">Product</h4>
              <ul className="space-y-2.5 text-sm text-[#424844]">
                <li><Link href="/dashboard" className="hover:text-[#476353] transition-colors">Features</Link></li>
                <li><Link href="/dashboard" className="hover:text-[#476353] transition-colors">Pricing</Link></li>
                <li><Link href="/dashboard" className="hover:text-[#476353] transition-colors">API Docs</Link></li>
              </ul>
            </div>
            <div className="space-y-4">
              <h4 className="text-sm font-bold text-[#191c1a] tracking-wide uppercase">Company</h4>
              <ul className="space-y-2.5 text-sm text-[#424844]">
                <li><Link href="/dashboard" className="hover:text-[#476353] transition-colors">About</Link></li>
                <li><Link href="/dashboard" className="hover:text-[#476353] transition-colors">Blog</Link></li>
                <li><Link href="/dashboard" className="hover:text-[#476353] transition-colors">Careers</Link></li>
              </ul>
            </div>
            <div className="space-y-4">
              <h4 className="text-sm font-bold text-[#191c1a] tracking-wide uppercase">Connect</h4>
              <ul className="space-y-2.5 text-sm text-[#424844]">
                <li><a href="#" className="hover:text-[#476353] transition-colors">Twitter</a></li>
                <li><a href="#" className="hover:text-[#476353] transition-colors">LinkedIn</a></li>
              </ul>
            </div>
          </div>
        </div>

        <div className="max-w-7xl mx-auto mt-12 pt-8 border-t border-[#e6e9e4]/40 flex flex-col md:flex-row justify-between items-center gap-4">
          <p className="text-xs text-[#424844]">© 2026 RecruitAI Inc. All rights reserved.</p>
          <div className="flex gap-6">
            <Link href="#" className="text-xs text-[#424844] hover:text-[#476353] transition-colors">Privacy Policy</Link>
            <Link href="#" className="text-xs text-[#424844] hover:text-[#476353] transition-colors">Terms of Service</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
