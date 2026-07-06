"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { Sparkles, ArrowRight, Mail, Lock, ShieldCheck, HelpCircle } from "lucide-react";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // If already logged in, redirect to dashboard
  useEffect(() => {
    if (typeof window !== "undefined") {
      const token = localStorage.getItem("token");
      if (token) {
        router.push("/dashboard");
      }
    }
  }, [router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      setError("Please fill in all fields.");
      return;
    }

    setError(null);
    setIsLoading(true);

    try {
      // Auth login endpoint expects application/x-www-form-urlencoded
      const params = new URLSearchParams();
      params.append("username", email);
      params.append("password", password);

      const response = await api.post("/auth/login", params, {
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
      });

      const { access_token } = response.data;
      localStorage.setItem("token", access_token);

      // Fetch user profile info
      const meResponse = await api.get("/auth/me");
      localStorage.setItem("user", JSON.stringify(meResponse.data));

      router.push("/dashboard");
    } catch (err: any) {
      console.error(err);
      if (err.response && err.response.data && err.response.data.detail) {
        setError(
          typeof err.response.data.detail === "string"
            ? err.response.data.detail
            : "Invalid credentials."
        );
      } else {
        setError("Login failed. Please check your backend connection.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#f7faf5] text-[#191c1a] font-sans flex items-center justify-center p-4 selection:bg-[#caead6] selection:text-[#314d3e]">
      
      {/* Decorative glows */}
      <div className="absolute top-10 left-1/4 w-80 h-80 bg-[#caead6]/30 rounded-full blur-[100px] pointer-events-none"></div>
      <div className="absolute bottom-10 right-1/4 w-96 h-96 bg-[#ffdad4]/30 rounded-full blur-[120px] pointer-events-none"></div>

      <div className="w-full max-w-md bg-white/70 backdrop-blur-lg p-8 md:p-10 rounded-[32px] border border-[#f0eae4] shadow-2xl shadow-[#5f7c6b]/5 relative z-10">
        
        {/* Brand Header */}
        <div className="text-center space-y-3 mb-8">
          <Link href="/" className="inline-flex items-center gap-2">
            <span className="text-2xl font-black tracking-tight text-[#476353]">RecruitAI</span>
          </Link>
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#caead6] text-[#314d3e] text-xs font-semibold">
            <Sparkles className="w-3.5 h-3.5" />
            Hiring Intelligence Portal
          </div>
          <h2 className="text-2xl font-extrabold tracking-tight text-[#191c1a]">Welcome back</h2>
          <p className="text-sm text-[#424844]">Enter credentials to access your talent workspace</p>
        </div>

        {error && (
          <div className="mb-5 p-3.5 bg-rose-500/10 border border-rose-500/30 text-[#994236] rounded-xl text-sm font-semibold">
            {error}
          </div>
        )}

        {/* Login Form */}
        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="space-y-1.5">
            <label className="text-xs font-bold text-[#191c1a] tracking-wider uppercase" htmlFor="email">
              Work Email
            </label>
            <div className="relative">
              <span className="absolute inset-y-0 left-0 pl-3.5 flex items-center text-[#727973]">
                <Mail className="w-5 h-5" />
              </span>
              <input
                id="email"
                type="email"
                required
                placeholder="you@company.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full pl-11 pr-4 py-3.5 bg-[#f1f4f0]/60 border border-[#c2c8c2] rounded-xl text-sm placeholder-[#727973] focus:outline-none focus:ring-2 focus:ring-[#476353] focus:border-transparent transition-all"
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <div className="flex justify-between items-center">
              <label className="text-xs font-bold text-[#191c1a] tracking-wider uppercase" htmlFor="password">
                Password
              </label>
              <a href="#forgot" className="text-xs font-semibold text-[#476353] hover:underline" onClick={(e) => e.preventDefault()}>
                Forgot password?
              </a>
            </div>
            <div className="relative">
              <span className="absolute inset-y-0 left-0 pl-3.5 flex items-center text-[#727973]">
                <Lock className="w-5 h-5" />
              </span>
              <input
                id="password"
                type="password"
                required
                placeholder="••••••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full pl-11 pr-4 py-3.5 bg-[#f1f4f0]/60 border border-[#c2c8c2] rounded-xl text-sm placeholder-[#727973] focus:outline-none focus:ring-2 focus:ring-[#476353] focus:border-transparent transition-all"
              />
            </div>
          </div>

          {/* Remember me */}
          <div className="flex items-center gap-2 py-1">
            <input
              id="remember"
              type="checkbox"
              className="w-4.5 h-4.5 text-[#476353] border-[#c2c8c2] rounded focus:ring-[#476353] cursor-pointer"
            />
            <label htmlFor="remember" className="text-xs text-[#424844] font-medium cursor-pointer">
              Remember me on this device
            </label>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={isLoading}
            className="w-full py-4 bg-[#476353] text-white font-semibold text-sm rounded-xl hover:bg-[#3d5446] disabled:bg-[#476353]/70 disabled:cursor-not-allowed transition-all duration-300 flex items-center justify-center gap-2 shadow-lg shadow-[#476353]/10"
          >
            {isLoading ? (
              <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
            ) : (
              <>
                Sign In to Dashboard
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </form>

        {/* Alternatives */}
        <div className="relative my-8 text-center">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-[#e6e9e4]"></div>
          </div>
          <span className="relative bg-white px-4 text-xs font-bold text-[#727973] uppercase tracking-widest">
            or continue with
          </span>
        </div>

        <button 
          onClick={() => router.push("/dashboard")}
          className="w-full py-3.5 border border-[#c2c8c2] bg-white hover:bg-[#f1f4f0]/50 rounded-xl text-sm font-semibold text-[#191c1a] flex items-center justify-center gap-2.5 transition-all"
        >
          Single Sign-On (OIDC)
        </button>

        {/* Footer info */}
        <div className="mt-8 pt-6 border-t border-[#e6e9e4]/60 flex items-center justify-between text-xs text-[#727973]">
          <div className="flex items-center gap-1.5">
            <ShieldCheck className="w-4 h-4 text-[#476353]" />
            Secure AES-256 data lock
          </div>
          <a href="#support" className="flex items-center gap-1 hover:text-[#476353] transition-colors" onClick={(e) => e.preventDefault()}>
            <HelpCircle className="w-4 h-4" />
            Support
          </a>
        </div>

      </div>
    </div>
  );
}
