'use client';

import { Suspense, useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { Shield, Loader2, CheckCircle, AlertTriangle } from 'lucide-react';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

function CallbackContent() {
  const searchParams = useSearchParams();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [error, setError] = useState('');

  useEffect(() => {
    const code = searchParams.get('code');
    if (!code) {
      setStatus('error');
      setError('No authorization code received from GitHub.');
      return;
    }

    fetch(`${API_BASE}/auth/github/callback?code=${code}`, { method: 'POST' })
      .then((res) => {
        if (!res.ok) throw new Error('Authentication failed');
        return res.json();
      })
      .then((data) => {
        localStorage.setItem('patchwatch_token', data.token);
        setStatus('success');
        setTimeout(() => { window.location.href = '/'; }, 1500);
      })
      .catch((e) => {
        setStatus('error');
        setError(e.message || 'Failed to authenticate with GitHub');
      });
  }, [searchParams]);

  return (
    <div className="relative z-10 text-center max-w-md mx-auto px-8">
      <Shield className="w-8 h-8 text-white/30 mx-auto mb-6" />

      {status === 'loading' && (
        <>
          <Loader2 className="w-6 h-6 text-white/50 animate-spin mx-auto mb-4" />
          <p className="text-sm font-mono text-white/50">AUTHENTICATING WITH GITHUB...</p>
          <div className="flex gap-1 justify-center mt-4">
            <div className="w-1 h-1 bg-white/40 rounded-full animate-pulse" />
            <div className="w-1 h-1 bg-white/30 rounded-full animate-pulse" style={{ animationDelay: '0.2s' }} />
            <div className="w-1 h-1 bg-white/20 rounded-full animate-pulse" style={{ animationDelay: '0.4s' }} />
          </div>
        </>
      )}

      {status === 'success' && (
        <>
          <CheckCircle className="w-6 h-6 text-[#00ff88] mx-auto mb-4" />
          <p className="text-sm font-mono text-[#00ff88]/70">AUTHENTICATION SUCCESSFUL</p>
          <p className="text-[10px] font-mono text-white/30 mt-2">Redirecting to dashboard...</p>
        </>
      )}

      {status === 'error' && (
        <>
          <AlertTriangle className="w-6 h-6 text-red-400 mx-auto mb-4" />
          <p className="text-sm font-mono text-red-400">AUTHENTICATION FAILED</p>
          <p className="text-[10px] font-mono text-white/30 mt-2">{error}</p>
          <a
            href="/"
            className="inline-block mt-6 text-xs font-mono text-white/40 border border-white/10 px-4 py-2 hover:border-white/30 transition-colors"
          >
            ← BACK TO HOME
          </a>
        </>
      )}
    </div>
  );
}

export default function AuthCallbackPage() {
  return (
    <main className="min-h-screen bg-black flex items-center justify-center">
      <div className="absolute inset-0 stars-bg" />
      <Suspense fallback={
        <div className="relative z-10 text-center">
          <Loader2 className="w-6 h-6 text-white/50 animate-spin mx-auto" />
        </div>
      }>
        <CallbackContent />
      </Suspense>
    </main>
  );
}
