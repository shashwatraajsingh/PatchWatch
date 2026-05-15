'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { Shield, Activity, GitCommit, Search, ArrowRight, Terminal, Scan, Webhook, LogIn, LogOut, GitBranch } from 'lucide-react';
import { fetchHealth } from '@/lib/api';
import { useAuth } from '@/lib/auth-context';

export default function HomePage() {
  const { user, loading: authLoading, login, logout } = useAuth();
  const [systemStatus, setSystemStatus] = useState<'checking' | 'online' | 'offline'>('checking');
  const [time, setTime] = useState('');

  useEffect(() => {
    fetchHealth()
      .then(() => setSystemStatus('online'))
      .catch(() => setSystemStatus('offline'));

    const tick = () => setTime(new Date().toISOString().replace('T', ' ').slice(0, 19) + ' UTC');
    tick();
    const interval = setInterval(tick, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <main className="relative min-h-screen overflow-hidden bg-black">
      <div className="absolute inset-0 w-full h-full stars-bg" />

      {/* Scanline */}
      <div className="absolute inset-0 pointer-events-none z-50 opacity-[0.03]">
        <div className="w-full h-[2px] bg-white animate-scanline" />
      </div>

      {/* Corner accents */}
      <div className="absolute top-0 left-0 w-12 h-12 border-t-2 border-l-2 border-white/30 z-20" />
      <div className="absolute top-0 right-0 w-12 h-12 border-t-2 border-r-2 border-white/30 z-20" />
      <div className="absolute bottom-0 left-0 w-12 h-12 border-b-2 border-l-2 border-white/30 z-20" />
      <div className="absolute bottom-0 right-0 w-12 h-12 border-b-2 border-r-2 border-white/30 z-20" />

      {/* Header */}
      <div className="absolute top-0 left-0 right-0 z-20 border-b border-white/10">
        <div className="container mx-auto px-8 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Shield className="w-5 h-5 text-white" />
              <span className="font-mono text-white text-xl font-bold tracking-[0.2em]">PATCHWATCH</span>
            </div>
            <div className="h-4 w-px bg-white/20" />
            <span className="text-white/40 text-[10px] font-mono">v1.0.0</span>
          </div>

          <div className="flex items-center gap-6 text-[10px] font-mono text-white/40">
            <span className="hidden sm:inline">{time}</span>
            <div className="flex items-center gap-2">
              <div className={`w-1.5 h-1.5 rounded-full ${
                systemStatus === 'online' ? 'bg-[#00ff88] animate-pulse' :
                systemStatus === 'offline' ? 'bg-red-500' : 'bg-yellow-500 animate-pulse'
              }`} />
              <span>{systemStatus === 'online' ? 'SYSTEM.ONLINE' : systemStatus === 'offline' ? 'SYSTEM.OFFLINE' : 'CHECKING...'}</span>
            </div>

            {/* Auth */}
            {!authLoading && (
              user ? (
                <div className="flex items-center gap-3">
                  <div className="flex items-center gap-2">
                    {user.avatar_url && (
                      <img src={user.avatar_url} alt="" className="w-5 h-5 rounded-full border border-white/20" />
                    )}
                    <span className="text-white/60">{user.username}</span>
                  </div>
                  <button onClick={logout} className="text-white/30 hover:text-white transition-colors flex items-center gap-1">
                    <LogOut className="w-3 h-3" />
                  </button>
                </div>
              ) : (
                <button onClick={login} className="flex items-center gap-2 text-white/50 hover:text-white border border-white/10 px-3 py-1 hover:border-white/30 transition-colors">
                  <GitBranch className="w-3 h-3" />
                  SIGN IN
                </button>
              )
            )}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="relative z-10 flex min-h-screen items-center justify-center">
        <div className="max-w-3xl mx-auto px-8 text-center">
          <div className="flex items-center gap-3 justify-center mb-6 opacity-40">
            <div className="w-16 h-px bg-white" />
            <Terminal className="w-3 h-3 text-white" />
            <div className="w-16 h-px bg-white" />
          </div>

          {/* ASCII title */}
          <pre className="text-white/20 text-[8px] leading-tight mb-6 hidden lg:block select-none">
{`██████╗  █████╗ ████████╗ ██████╗██╗  ██╗██╗    ██╗ █████╗ ████████╗ ██████╗██╗  ██╗
██╔══██╗██╔══██╗╚══██╔══╝██╔════╝██║  ██║██║    ██║██╔══██╗╚══██╔══╝██╔════╝██║  ██║
██████╔╝███████║   ██║   ██║     ███████║██║ █╗ ██║███████║   ██║   ██║     ███████║
██╔═══╝ ██╔══██║   ██║   ██║     ██╔══██║██║███╗██║██╔══██║   ██║   ██║     ██╔══██║
██║     ██║  ██║   ██║   ╚██████╗██║  ██║╚███╔███╔╝██║  ██║   ██║   ╚██████╗██║  ██║
╚═╝     ╚═╝  ╚═╝   ╚═╝    ╚═════╝╚═╝  ╚═╝ ╚══╝╚══╝ ╚═╝  ╚═╝   ╚═╝    ╚═════╝╚═╝  ╚═╝`}
          </pre>

          <h1 className="text-4xl lg:text-6xl font-bold text-white mb-4 tracking-[0.15em] font-mono lg:hidden">
            PATCHWATCH
          </h1>

          <p className="text-white/50 text-sm font-mono mb-2 tracking-wider">
            AI-POWERED SECURITY VULNERABILITY SCANNER
          </p>

          <div className="flex gap-1 justify-center mb-8 opacity-30">
            {Array.from({ length: 60 }).map((_, i) => (
              <div key={i} className="w-0.5 h-0.5 bg-white rounded-full" />
            ))}
          </div>

          <p className="text-white/40 text-xs font-mono max-w-lg mx-auto mb-10 leading-relaxed">
            Every push to GitHub triggers an automated security scan. Two AI models analyze your code changes in parallel,
            tracking vulnerabilities across commits — what&apos;s new, what&apos;s recurring, what&apos;s resolved.
          </p>

          {/* Action buttons — show login if not authenticated */}
          {user ? (
            <div className="flex flex-col sm:flex-row gap-4 justify-center mb-16">
              <Link href="/scan" className="group relative px-8 py-3 border border-white text-white font-mono text-sm hover:bg-white hover:text-black transition-all duration-200 flex items-center justify-center gap-3">
                <span className="absolute -top-1 -left-1 w-2 h-2 border-t border-l border-white opacity-0 group-hover:opacity-100 transition-opacity" />
                <span className="absolute -bottom-1 -right-1 w-2 h-2 border-b border-r border-white opacity-0 group-hover:opacity-100 transition-opacity" />
                <Scan className="w-4 h-4" />
                INITIATE SCAN
              </Link>

              <Link href="/reports" className="group relative px-8 py-3 border border-white/30 text-white/70 font-mono text-sm hover:border-white hover:text-white transition-all duration-200 flex items-center justify-center gap-3">
                <Activity className="w-4 h-4" />
                VIEW REPORTS
              </Link>

              <Link href="/repos" className="group relative px-8 py-3 border border-white/30 text-white/70 font-mono text-sm hover:border-white hover:text-white transition-all duration-200 flex items-center justify-center gap-3">
                <Webhook className="w-4 h-4" />
                AUTO SCAN
                <ArrowRight className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity" />
              </Link>
            </div>
          ) : (
            <div className="mb-16">
              <button
                onClick={login}
                className="group relative px-10 py-3 border border-white text-white font-mono text-sm hover:bg-white hover:text-black transition-all duration-200 flex items-center justify-center gap-3 mx-auto"
              >
                <span className="absolute -top-1 -left-1 w-2 h-2 border-t border-l border-white opacity-0 group-hover:opacity-100 transition-opacity" />
                <span className="absolute -bottom-1 -right-1 w-2 h-2 border-b border-r border-white opacity-0 group-hover:opacity-100 transition-opacity" />
                <GitBranch className="w-4 h-4" />
                SIGN IN WITH GITHUB
              </button>
              <p className="text-white/20 text-[10px] font-mono mt-3">Sign in to scan your repositories</p>
            </div>
          )}

          {/* Feature cards */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 max-w-xl mx-auto">
            {[
              { icon: GitCommit, label: 'WEBHOOK', desc: 'POST /webhook/github' },
              { icon: Search, label: 'SCANNER', desc: 'MiniMax M2.7 + Qwen 3' },
              { icon: Shield, label: 'MEMORY', desc: 'Cross-commit tracking' },
            ].map(({ icon: Icon, label, desc }) => (
              <div key={label} className="border border-white/10 p-4 hover:border-white/30 transition-colors group">
                <Icon className="w-4 h-4 text-white/40 mb-2 group-hover:text-white/70 transition-colors" />
                <div className="text-[10px] text-white/60 font-mono tracking-wider">{label}</div>
                <div className="text-[9px] text-white/30 font-mono mt-1">{desc}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Bottom bar */}
      <div className="absolute bottom-0 left-0 right-0 z-20 border-t border-white/10">
        <div className="container mx-auto px-8 py-3 flex items-center justify-between">
          <div className="flex items-center gap-4 text-[9px] font-mono text-white/30">
            <span>PROTOCOL.ACTIVE</span>
            <div className="flex gap-0.5">
              {Array.from({ length: 8 }).map((_, i) => (
                <div key={i} className="w-1 bg-white/20" style={{ height: `${Math.random() * 12 + 4}px` }} />
              ))}
            </div>
          </div>
          <div className="flex items-center gap-3 text-[9px] font-mono text-white/30">
            <span>◐ MONITORING</span>
            <div className="flex gap-1">
              <div className="w-1 h-1 bg-white/40 rounded-full animate-pulse" />
              <div className="w-1 h-1 bg-white/30 rounded-full animate-pulse" style={{ animationDelay: '0.2s' }} />
              <div className="w-1 h-1 bg-white/20 rounded-full animate-pulse" style={{ animationDelay: '0.4s' }} />
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
