'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { Shield, ArrowLeft, AlertTriangle, CheckCircle, GitCommit, Clock, FileCode, ChevronDown, ChevronRight, ExternalLink } from 'lucide-react';
import { fetchReport, ScanReport, Vulnerability } from '@/lib/api';

function SeverityBadge({ severity }: { severity: string }) {
  const colors: Record<string, string> = {
    critical: 'text-[#ff3333] bg-[#ff3333]/10 border-[#ff3333]/20',
    high: 'text-[#ff8800] bg-[#ff8800]/10 border-[#ff8800]/20',
    medium: 'text-[#ffcc00] bg-[#ffcc00]/10 border-[#ffcc00]/20',
    low: 'text-[#3388ff] bg-[#3388ff]/10 border-[#3388ff]/20',
    info: 'text-white/40 bg-white/5 border-white/10',
  };
  return (
    <span className={`text-[10px] font-mono px-2 py-0.5 border ${colors[severity] || colors.info}`}>
      {severity.toUpperCase()}
    </span>
  );
}

function VulnCard({ vuln, isNew }: { vuln: Vulnerability; isNew: boolean }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="border border-white/10 hover:border-white/20 transition-colors">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full p-4 text-left flex items-start gap-3"
      >
        <div className="mt-0.5">
          {expanded ? <ChevronDown className="w-3 h-3 text-white/30" /> : <ChevronRight className="w-3 h-3 text-white/30" />}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1 flex-wrap">
            <SeverityBadge severity={vuln.severity} />
            <span className="text-xs font-mono text-white/70">{vuln.category}</span>
            {isNew && (
              <span className="text-[9px] font-mono text-[#00ff88] bg-[#00ff88]/10 border border-[#00ff88]/20 px-1.5 py-0.5">NEW</span>
            )}
          </div>
          <div className="text-[10px] font-mono text-white/30 flex items-center gap-2">
            <FileCode className="w-3 h-3" />
            {vuln.file}
            {vuln.line && <span>:{vuln.line}</span>}
          </div>
        </div>
      </button>

      {expanded && (
        <div className="px-4 pb-4 pl-10 space-y-3 border-t border-white/5 pt-3">
          <p className="text-xs font-mono text-white/50 leading-relaxed">{vuln.description}</p>

          {vuln.code_snippet && (
            <div className="bg-white/[0.03] border border-white/5 p-3 overflow-x-auto">
              <pre className="text-[11px] font-mono text-white/60">{vuln.code_snippet}</pre>
            </div>
          )}

          <div className="border-l-2 border-[#00ff88]/30 pl-3">
            <span className="text-[9px] font-mono text-[#00ff88]/60 tracking-wider">RECOMMENDATION</span>
            <p className="text-xs font-mono text-white/40 mt-1">{vuln.recommendation}</p>
          </div>
        </div>
      )}
    </div>
  );
}

export default function ReportDetailPage() {
  const params = useParams();
  const [report, setReport] = useState<ScanReport | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const id = Number(params.id);
    if (!id) return;
    fetchReport(id)
      .then(setReport)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [params.id]);

  if (loading) {
    return (
      <main className="min-h-screen bg-black flex items-center justify-center">
        <div className="text-white/30 text-xs font-mono animate-pulse">LOADING REPORT...</div>
      </main>
    );
  }

  if (!report) {
    return (
      <main className="min-h-screen bg-black flex items-center justify-center">
        <div className="text-center">
          <Shield className="w-8 h-8 text-white/10 mx-auto mb-4" />
          <p className="text-white/30 text-sm font-mono">REPORT NOT FOUND</p>
          <Link href="/reports" className="text-xs font-mono text-white/20 hover:text-white/50 mt-4 inline-block">
            ← BACK TO REPORTS
          </Link>
        </div>
      </main>
    );
  }

  const totalVulns = Object.values(report.severity_summary).reduce((a, b) => a + b, 0);
  const newIds = new Set(report.new_issues.map(v => v.id));

  return (
    <main className="min-h-screen bg-black relative">
      <div className="absolute inset-0 stars-bg" />

      {/* Header */}
      <div className="relative z-10 border-b border-white/10">
        <div className="container mx-auto px-8 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/reports" className="text-white/40 hover:text-white transition-colors">
              <ArrowLeft className="w-4 h-4" />
            </Link>
            <div className="h-4 w-px bg-white/10" />
            <Shield className="w-4 h-4 text-white/60" />
            <span className="font-mono text-white text-sm tracking-[0.15em]">PATCHWATCH</span>
            <div className="h-4 w-px bg-white/10" />
            <span className="text-white/30 text-[10px] font-mono tracking-wider">REPORT #{report.id}</span>
          </div>
        </div>
      </div>

      <div className="relative z-10 container mx-auto px-8 py-8 max-w-4xl">
        {/* Report header */}
        <div className="border border-white/10 p-6 mb-6">
          <div className="flex items-start justify-between mb-4">
            <div>
              <h1 className="text-lg font-mono font-bold text-white tracking-wider mb-1">{report.repo_full_name}</h1>
              <div className="flex items-center gap-3 text-[10px] font-mono text-white/30">
                <span className="border border-white/10 px-1.5 py-0.5">{report.branch}</span>
                <span className="flex items-center gap-1"><GitCommit className="w-3 h-3" />{report.commit_sha.slice(0, 8)}</span>
                <span className="flex items-center gap-1"><Clock className="w-3 h-3" />{new Date(report.created_at).toLocaleString()}</span>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {totalVulns === 0 ? (
                <CheckCircle className="w-5 h-5 text-[#00ff88]/60" />
              ) : (
                <AlertTriangle className="w-5 h-5 text-[#ff8800]/60" />
              )}
            </div>
          </div>

          {report.commit_message && (
            <p className="text-xs font-mono text-white/30 mb-4 border-l-2 border-white/10 pl-3">{report.commit_message}</p>
          )}

          {/* Stats */}
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
            {[
              { label: 'FILES', value: report.files_scanned },
              { label: 'TOTAL', value: totalVulns },
              { label: 'NEW', value: report.new_issues.length, color: report.new_issues.length > 0 ? 'text-[#ff8800]' : '' },
              { label: 'RESOLVED', value: report.resolved_issues.length, color: report.resolved_issues.length > 0 ? 'text-[#00ff88]' : '' },
              { label: 'DURATION', value: `${report.scan_duration_ms}ms` },
            ].map(({ label, value, color }) => (
              <div key={label} className="border border-white/5 p-3">
                <div className="text-[9px] text-white/30 font-mono tracking-wider">{label}</div>
                <div className={`text-lg font-mono mt-1 ${color || 'text-white'}`}>{value}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Severity breakdown */}
        <div className="flex gap-3 mb-6">
          {(Object.entries(report.severity_summary) as [string, number][]).map(([sev, count]) => {
            const colors: Record<string, string> = {
              critical: 'border-[#ff3333]/30 text-[#ff3333]',
              high: 'border-[#ff8800]/30 text-[#ff8800]',
              medium: 'border-[#ffcc00]/20 text-[#ffcc00]',
              low: 'border-[#3388ff]/20 text-[#3388ff]',
              info: 'border-white/10 text-white/30',
            };
            return (
              <div key={sev} className={`flex-1 border ${colors[sev]} p-3 text-center`}>
                <div className="text-lg font-mono">{count}</div>
                <div className="text-[9px] font-mono opacity-60 tracking-wider">{sev.toUpperCase()}</div>
              </div>
            );
          })}
        </div>

        {/* Comparison section */}
        {(report.new_issues.length > 0 || report.resolved_issues.length > 0 || report.recurring_issues.length > 0) && (
          <div className="flex gap-3 mb-6 text-[10px] font-mono">
            {report.new_issues.length > 0 && (
              <div className="flex items-center gap-1.5 text-[#ff8800]/70 bg-[#ff8800]/5 border border-[#ff8800]/10 px-3 py-1.5">
                🆕 {report.new_issues.length} NEW
              </div>
            )}
            {report.resolved_issues.length > 0 && (
              <div className="flex items-center gap-1.5 text-[#00ff88]/70 bg-[#00ff88]/5 border border-[#00ff88]/10 px-3 py-1.5">
                ✅ {report.resolved_issues.length} RESOLVED
              </div>
            )}
            {report.recurring_issues.length > 0 && (
              <div className="flex items-center gap-1.5 text-white/40 bg-white/5 border border-white/10 px-3 py-1.5">
                🔁 {report.recurring_issues.length} RECURRING
              </div>
            )}
          </div>
        )}

        {/* Vulnerabilities */}
        {report.vulnerabilities.length === 0 ? (
          <div className="border border-[#00ff88]/10 bg-[#00ff88]/[0.02] p-8 text-center">
            <CheckCircle className="w-8 h-8 text-[#00ff88]/30 mx-auto mb-3" />
            <p className="text-sm font-mono text-[#00ff88]/50">NO VULNERABILITIES DETECTED</p>
            <p className="text-[10px] font-mono text-white/20 mt-1">This commit looks clean.</p>
          </div>
        ) : (
          <div className="space-y-2">
            <div className="flex items-center gap-2 mb-4 opacity-40">
              <div className="w-8 h-px bg-white" />
              <AlertTriangle className="w-3 h-3 text-white" />
              <span className="text-[10px] font-mono text-white">VULNERABILITIES</span>
              <div className="flex-1 h-px bg-white" />
            </div>
            {report.vulnerabilities.map((vuln, i) => (
              <VulnCard key={vuln.id || i} vuln={vuln} isNew={newIds.has(vuln.id)} />
            ))}
          </div>
        )}
      </div>
    </main>
  );
}
