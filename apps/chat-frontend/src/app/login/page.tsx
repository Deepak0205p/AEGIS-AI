'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/useAuthStore';
import { useThemeStore } from '@/store/useThemeStore';
import { RevealBrand, RevealLogoIcon } from '@/components/RevealLogo';
import {
  ShieldCheck,
  ArrowRight,
  Loader2,
  Lock,
  User,
  AlertCircle,
  Eye,
  EyeOff,
  Sun,
  Moon,
  Building2,
  KeyRound,
  CheckCircle2
} from 'lucide-react';

export default function LoginPage() {
  const router = useRouter();
  const { login, isAuthenticated, isLoading: isAuthLoading, initialize: initAuth } = useAuthStore();
  const { theme, toggleTheme } = useThemeStore();
  const isDark = theme === 'dark';

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    initAuth();
  }, [initAuth]);

  useEffect(() => {
    if (!isAuthLoading && isAuthenticated) {
      router.replace('/');
    }
  }, [isAuthLoading, isAuthenticated, router]);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const savedUser = localStorage.getItem('reveal_saved_username');
      if (savedUser) {
        setUsername(savedUser);
        setRememberMe(true);
      }
    }
  }, []);

  const handleLogin = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const cleanUser = username.trim();
    const cleanPass = password.trim();
    if (!cleanUser || !cleanPass) {
      setError('Please enter both your Username and Password.');
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      const res = await fetch(`http://${window.location.hostname}:8000/api/v1/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username: cleanUser,
          password: cleanPass,
        }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || 'Invalid username or password.');
      }
      const data = await res.json();

      // Save username if rememberMe is enabled
      if (typeof window !== 'undefined') {
        if (rememberMe) {
          localStorage.setItem('reveal_saved_username', cleanUser);
        } else {
          localStorage.removeItem('reveal_saved_username');
        }

        // Trigger Browser Credential Manager / Password Store (Chrome, Edge, Firefox)
        if ('PasswordCredential' in window && navigator.credentials) {
          try {
            const cred = new (window as any).PasswordCredential({
              id: cleanUser,
              password: cleanPass,
              name: data.user?.full_name || cleanUser,
            });
            await navigator.credentials.store(cred);
          } catch (credErr) {
            // Non-critical, ignore if user cancels or browser policies reject
          }
        }
      }

      login(data.user, data.token);
      router.replace('/');
    } catch (err: any) {
      setError(err.message || 'Authentication failed. Please check your credentials.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="relative min-h-[100dvh] w-full flex flex-col justify-between bg-slate-50 text-slate-900 dark:bg-[#08080a] dark:text-[#e3e3e3] font-sans antialiased selection:bg-blue-500/20 dark:selection:bg-[#4285f4]/30 overflow-x-hidden transition-colors duration-300">
      
      {/* Dynamic Ambient Aurora Background matching Chat Header */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden z-0">
        <div className="absolute -top-[25%] left-1/2 -translate-x-1/2 w-[800px] h-[450px] bg-gradient-to-b from-blue-500/10 via-purple-500/5 to-transparent dark:from-blue-600/15 dark:via-purple-600/10 dark:to-transparent rounded-full blur-[120px]" />
        <div className="absolute -bottom-[20%] right-[-10%] w-[600px] h-[400px] bg-emerald-500/5 dark:bg-emerald-600/10 rounded-full blur-[140px]" />
      </div>

      {/* Top Header & Air-gap Status Banner */}
      <header className="relative z-10 w-full max-w-7xl mx-auto flex items-center justify-between px-6 py-4 border-b border-slate-200/80 dark:border-white/[0.06] backdrop-blur-md">
        <div className="flex items-center gap-4">
          <RevealBrand size="md" showBadge={true} />
          

        </div>

        {/* Right Header Actions: Theme Switcher & Air-gap Badge */}
        <div className="flex items-center gap-3">
          <button
            onClick={toggleTheme}
            aria-label="Toggle theme"
            className="h-9 w-9 rounded-full bg-white hover:bg-slate-100 dark:bg-[#141418] dark:hover:bg-[#1e1e24] border border-slate-200 dark:border-white/10 text-slate-700 dark:text-[#c4c7c5] flex items-center justify-center transition-all shadow-xs cursor-pointer active:scale-95"
          >
            {isDark ? <Sun className="h-4 w-4 text-amber-400" /> : <Moon className="h-4 w-4 text-blue-600" />}
          </button>

          
        </div>
      </header>

      {/* Main Authentication Section */}
      <main className="relative z-10 w-full max-w-md mx-auto my-auto px-4 py-8 sm:py-12 flex flex-col items-center">
        
        {/* Brand Hero Greeting */}
        <div className="text-center mb-8 space-y-3 flex flex-col items-center">
                
          <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 dark:from-[#4285f4] dark:via-[#9b72cf] dark:to-[#d96570] bg-clip-text text-transparent">
            Sign In to AEGIS AI
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 dark:text-[#8e918f] font-normal max-w-xs leading-relaxed">
            Enter your refinery operational credentials to access the sovereign intelligence workbench
          </p>
        </div>

        {/* Clean Modern Card Container */}
        <div className="w-full bg-white dark:bg-[#101115] rounded-3xl border border-slate-200/90 dark:border-white/[0.08] shadow-[0_4px_24px_rgba(0,0,0,0.04),0_12px_48px_rgba(0,0,0,0.04)] dark:shadow-[0_8px_40px_rgba(0,0,0,0.6)] p-6 sm:p-8 backdrop-blur-xl">
          
          {/* Error Alert Box */}
          {error && (
            <div className="mb-5 p-3 rounded-2xl bg-red-50 border border-red-200/80 text-red-700 dark:bg-red-950/30 dark:border-red-500/30 dark:text-red-300 text-xs flex items-start gap-2.5 animate-in fade-in duration-200">
              <AlertCircle className="w-4 h-4 text-red-500 shrink-0 mt-0.5" />
              <div className="flex-1 leading-relaxed font-medium">{error}</div>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleLogin} method="POST" action="#" autoComplete="on" className="space-y-4">
            
            {/* Username Input */}
            <div className="space-y-1.5">
              <label htmlFor="username" className="block text-xs font-semibold text-slate-700 dark:text-[#c4c7c5]">
                Username / Operator ID
              </label>
              <div className="relative">
                <input
                  id="username"
                  name="username"
                  type="text"
                  autoComplete="username"
                  autoCapitalize="none"
                  spellCheck={false}
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="e.g. operator or admin"
                  autoFocus
                  required
                  className="w-full pl-10 pr-3.5 py-2.5 text-sm bg-slate-50 dark:bg-[#15161c] border border-slate-200 dark:border-white/[0.08] rounded-xl focus:outline-none focus:border-blue-500 dark:focus:border-[#a8c7fa] text-slate-900 dark:text-[#e3e3e3] placeholder-slate-400 dark:placeholder-[#6e7175] transition-all"
                />
                <User className="w-4 h-4 absolute left-3.5 top-3 text-slate-400 dark:text-[#6e7175]" />
              </div>
            </div>

            {/* Password Input */}
            <div className="space-y-1.5">
              <label htmlFor="password" className="block text-xs font-semibold text-slate-700 dark:text-[#c4c7c5]">
                Account Password
              </label>
              <div className="relative">
                <input
                  id="password"
                  name="password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="current-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  required
                  className="w-full pl-10 pr-10 py-2.5 text-sm bg-slate-50 dark:bg-[#15161c] border border-slate-200 dark:border-white/[0.08] rounded-xl focus:outline-none focus:border-blue-500 dark:focus:border-[#a8c7fa] text-slate-900 dark:text-[#e3e3e3] placeholder-slate-400 dark:placeholder-[#6e7175] transition-all"
                />
                <Lock className="w-4 h-4 absolute left-3.5 top-3 text-slate-400 dark:text-[#6e7175]" />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3.5 top-3 text-slate-400 hover:text-slate-600 dark:text-[#6e7175] dark:hover:text-[#c4c7c5] cursor-pointer"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {/* Remember Me / Device Save Option */}
            <div className="flex items-center justify-between pt-1">
              <label htmlFor="rememberMe" className="flex items-center gap-2 cursor-pointer select-none text-xs text-slate-600 dark:text-[#a8abb3] hover:text-slate-900 dark:hover:text-white transition-colors">
                <input
                  id="rememberMe"
                  name="rememberMe"
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  className="w-4 h-4 rounded-md border-slate-300 dark:border-white/20 bg-slate-100 dark:bg-[#15161c] text-blue-600 focus:ring-blue-500 cursor-pointer accent-blue-600"
                />
                <span>Remember me on this browser</span>
              </label>
            </div>

            {/* Submit CTA */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full flex items-center justify-center gap-2 py-3 px-4 rounded-xl bg-[#0070f3] hover:bg-[#0060df] active:scale-[0.98] disabled:opacity-50 text-white font-bold text-sm transition-all shadow-md shadow-blue-500/20 cursor-pointer mt-2"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Authenticating...</span>
                </>
              ) : (
                <>
                  <span>Sign In</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>
        </div>
      </main>

      
    </div>
  );
}


