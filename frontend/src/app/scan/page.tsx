'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Shield, ArrowLeft, Scan, Loader2, AlertTriangle, CheckCircle, GitBranch, GitCommit } from 'lucide-react';
import { triggerScan, ManualScanResponse } from '@/lib/api';

export default function ScanPage() {
  const [repo, setRepo] = useState('');
  const [sha, setSha] = useState('');
  const [branch, setBranch] = useState('main');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ManualScanResponse | null>(null);
  const [error, setError] = useState('');

  const handleScan = async () => {
    if (!repo || !sha) return;
    setLoading(true);
    setError('');
    setResult(null);

    try {
      const res = await triggerScan({ repo_full_name: repo, commit_sha: sha, branch });
      setResult(res);
    } catch (e) {
      setError('Scan failed. Check if the repo and commit SHA are valid.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-black relative">
      {/* Stars */}
      <div className="absolute inset-0 stars-bg" />
      
      {/* Corner accents */}
      <div className="absolute top-0 left-0 w-8 h-8 border-t-2 border-l-2 border-white/20 z-20" />
      <div className="absolute top-0 right-0 w-8 h-8 border-t-2 border-r-2 border-white/20 z-20" />

      {/* Header */}
      <div className="relative z-10 border-b border-white/10">
        <div className="container mx-auto px-8 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/" className="flex items-center gap-2 text-white/40 hover:text-white transition-colors">
              <ArrowLeft className="w-4 h-4" />
            </Link>
            <div className="h-4 w-px bg-white/10" />
            <Shield className="w-4 h-4 text-white/60" />
            <span className="font-mono text-white text-sm tracking-[0.15em]">PATCHWATCH</span>
            <div className="h-4 w-px bg-white/10" />
            <span className="text-white/30 text-[10px] font-mono tracking-wider">MANUAL SCAN</span>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="relative z-10 container mx-auto px-8 py-12 max-w-2xl">
        {/* Title */}
        <div className="mb-10">
          <div className="flex items-center gap-2 mb-3 opacity-40">
            <div className="w-8 h-px bg-white" />
            <Scan className="w-3 h-3 text-white" />
            <div className="flex-1 h-px bg-white" />
          </div>
          <h1 className="text-2xl font-mono font-bold text-white tracking-wider mb-2">INITIATE SCAN</h1>
          <p className="text-white/30 text-xs font-mono">Manually scan any public repository commit for security vulnerabilities.</p>
        </div>

        {/* Form */}
        <div className="space-y-6">
          <div>
            <label className="block text-[10px] font-mono text-white/50 tracking-wider mb-2">REPOSITORY</label>
            <div className="relative">
              <GitBranch className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/20" />
              <input
                type="text"
                value={repo}
                onChange={(e) => setRepo(e.target.value)}
                placeholder="owner/repo"
                className="w-full bg-white/[0.03] border border-white/10 text-white font-mono text-sm px-10 py-3 placeholder:text-white/20 focus:border-white/30 focus:outline-none transition-colors"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-[10px] font-mono text-white/50 tracking-wider mb-2">COMMIT SHA</label>
              <div className="relative">
                <GitCommit className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/20" />
                <input
                  type="text"
                  value={sha}
                  onChange={(e) => setSha(e.target.value)}
                  placeholder="abc123..."
                  className="w-full bg-white/[0.03] border border-white/10 text-white font-mono text-sm px-10 py-3 placeholder:text-white/20 focus:border-white/30 focus:outline-none transition-colors"
                />
              </div>
            </div>

            <div>
              <label className="block text-[10px] font-mono text-white/50 tracking-wider mb-2">BRANCH</label>
              <input
                type="text"
                value={branch}
                onChange={(e) => setBranch(e.target.value)}
                className="w-full bg-white/[0.03] border border-white/10 text-white font-mono text-sm px-4 py-3 placeholder:text-white/20 focus:border-white/30 focus:outline-none transition-colors"
              />
            </div>
          </div>

          <button
            onClick={handleScan}
            disabled={loading || !repo || !sha}
            className="w-full relative px-8 py-3 border border-white text-white font-mono text-sm hover:bg-white hover:text-black transition-all duration-200 disabled:opacity-30 disabled:cursor-not-allowed flex items-center justify-center gap-3 group"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                SCANNING...
              </>
            ) : (
              <>
                <Scan className="w-4 h-4" />
                EXECUTE SCAN
              </>
            )}
            <span className="absolute -top-1 -left-1 w-2 h-2 border-t border-l border-white opacity-0 group-hover:opacity-100 transition-opacity" />
            <span className="absolute -bottom-1 -right-1 w-2 h-2 border-b border-r border-white opacity-0 group-hover:opacity-100 transition-opacity" />
          </button>
        </div>

        {/* Error */}
        {error && (
          <div className="mt-8 border border-red-500/30 bg-red-500/5 p-4 flex items-start gap-3">
            <AlertTriangle className="w-4 h-4 text-red-500 mt-0.5 shrink-0" />
            <p className="text-red-400 text-xs font-mono">{error}</p>
          </div>
        )}

        {/* Loading state */}
        {loading && (
          <div className="mt-8 border border-white/10 p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-2 h-2 bg-white/40 rounded-full animate-pulse" />
              <span className="text-[10px] font-mono text-white/50 tracking-wider">SCAN IN PROGRESS</span>
            </div>
            <div className="space-y-2">
              {['Fetching commit from GitHub...', 'Parsing changed files...', 'Running AI security scan...', 'Generating report...'].map((step, i) => (
                <div key={i} className="flex items-center gap-2 text-xs font-mono text-white/30">
                  <span className="text-white/20">{'>'}</span>
                  {step}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Result */}
        {result && (
          <div className="mt-8 space-y-4">
            <div className="flex items-center gap-2 opacity-40">
              <div className="w-8 h-px bg-white" />
              <span className="text-[10px] font-mono text-white">RESULT</span>
              <div className="flex-1 h-px bg-white" />
            </div>

            <div className="border border-white/10 p-6">
              {/* Status */}
              <div className="flex items-center gap-3 mb-6">
                {result.vulnerabilities_found === 0 ? (
                  <CheckCircle className="w-5 h-5 text-[#00ff88]" />
                ) : (
                  <AlertTriangle className="w-5 h-5 text-[#ff8800]" />
                )}
                <span className="font-mono text-sm text-white">
                  {result.vulnerabilities_found === 0 ? 'NO VULNERABILITIES DETECTED' : `${result.vulnerabilities_found} VULNERABILITY(S) FOUND`}
                </span>
              </div>

              {/* Stats grid */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
                {[
                  { label: 'FILES', value: result.files_scanned ?? 0 },
                  { label: 'ISSUES', value: result.vulnerabilities_found ?? 0 },
                  { label: 'DURATION', value: `${result.scan_duration_ms ?? 0}ms` },
                  { label: 'NEW', value: result.new_issues ?? 0 },
                ].map(({ label, value }) => (
                  <div key={label} className="border border-white/5 p-3">
                    <div className="text-[9px] text-white/30 font-mono tracking-wider">{label}</div>
                    <div className="text-lg text-white font-mono mt-1">{value}</div>
                  </div>
                ))}
              </div>

              {/* Severity */}
              {result.severity_summary && (
                <div className="flex gap-4 mb-6">
                  {Object.entries(result.severity_summary).map(([sev, count]) => (
                    <div key={sev} className="flex items-center gap-2">
                      <div className={`w-2 h-2 rounded-full ${
                        sev === 'critical' ? 'bg-[#ff3333]' :
                        sev === 'high' ? 'bg-[#ff8800]' :
                        sev === 'medium' ? 'bg-[#ffcc00]' :
                        sev === 'low' ? 'bg-[#3388ff]' : 'bg-white/20'
                      }`} />
                      <span className="text-[10px] font-mono text-white/40">{sev.toUpperCase()}: {count}</span>
                    </div>
                  ))}
                </div>
              )}

              {/* Link to full report */}
              {result.report_id && (
                <Link
                  href={`/reports/${result.report_id}`}
                  className="inline-flex items-center gap-2 text-xs font-mono text-white/50 hover:text-white border border-white/10 px-4 py-2 hover:border-white/30 transition-colors"
                >
                  VIEW FULL REPORT →
                </Link>
              )}
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
