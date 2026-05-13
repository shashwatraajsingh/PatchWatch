'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Shield, ArrowLeft, Activity, GitCommit, AlertTriangle, CheckCircle, Clock, FileCode } from 'lucide-react';
import { fetchReports, ScanReportListItem } from '@/lib/api';

export default function ReportsPage() {
  const [reports, setReports] = useState<ScanReportListItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchReports()
      .then(setReports)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const totalVulns = (r: ScanReportListItem) =>
    Object.values(r.severity_summary).reduce((a, b) => a + b, 0);

  const severityColor = (r: ScanReportListItem) => {
    if (r.severity_summary.critical > 0) return 'border-[#ff3333]/30';
    if (r.severity_summary.high > 0) return 'border-[#ff8800]/30';
    if (r.severity_summary.medium > 0) return 'border-[#ffcc00]/20';
    return 'border-white/10';
  };

  const timeAgo = (dateStr: string) => {
    const diff = Date.now() - new Date(dateStr).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 60) return `${mins}m ago`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}h ago`;
    return `${Math.floor(hours / 24)}d ago`;
  };

  return (
    <main className="min-h-screen bg-black relative">
      <div className="absolute inset-0 stars-bg" />

      {/* Corner accents */}
      <div className="absolute top-0 left-0 w-8 h-8 border-t-2 border-l-2 border-white/20 z-20" />
      <div className="absolute top-0 right-0 w-8 h-8 border-t-2 border-r-2 border-white/20 z-20" />

      {/* Header */}
      <div className="relative z-10 border-b border-white/10">
        <div className="container mx-auto px-8 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/" className="text-white/40 hover:text-white transition-colors">
              <ArrowLeft className="w-4 h-4" />
            </Link>
            <div className="h-4 w-px bg-white/10" />
            <Shield className="w-4 h-4 text-white/60" />
            <span className="font-mono text-white text-sm tracking-[0.15em]">PATCHWATCH</span>
            <div className="h-4 w-px bg-white/10" />
            <span className="text-white/30 text-[10px] font-mono tracking-wider">SCAN REPORTS</span>
          </div>
          <Link href="/scan" className="text-[10px] font-mono text-white/40 hover:text-white border border-white/10 px-3 py-1.5 hover:border-white/30 transition-colors">
            + NEW SCAN
          </Link>
        </div>
      </div>

      {/* Content */}
      <div className="relative z-10 container mx-auto px-8 py-8 max-w-4xl">
        <div className="flex items-center gap-2 mb-6 opacity-40">
          <div className="w-8 h-px bg-white" />
          <Activity className="w-3 h-3 text-white" />
          <div className="flex-1 h-px bg-white" />
        </div>

        {loading ? (
          <div className="space-y-3">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="border border-white/5 p-5 animate-pulse">
                <div className="h-3 bg-white/5 w-1/3 mb-3" />
                <div className="h-2 bg-white/5 w-2/3" />
              </div>
            ))}
          </div>
        ) : reports.length === 0 ? (
          <div className="border border-white/10 p-12 text-center">
            <Shield className="w-8 h-8 text-white/10 mx-auto mb-4" />
            <p className="text-white/30 text-sm font-mono mb-2">NO REPORTS YET</p>
            <p className="text-white/15 text-xs font-mono mb-6">Run your first scan to see results here.</p>
            <Link href="/scan" className="text-xs font-mono text-white/50 hover:text-white border border-white/20 px-4 py-2 hover:border-white/40 transition-colors">
              INITIATE FIRST SCAN →
            </Link>
          </div>
        ) : (
          <div className="space-y-2">
            {reports.map((report) => (
              <Link
                key={report.id}
                href={`/reports/${report.id}`}
                className={`block border ${severityColor(report)} p-5 hover:bg-white/[0.02] transition-all group`}
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-3">
                    {totalVulns(report) === 0 ? (
                      <CheckCircle className="w-4 h-4 text-[#00ff88]/60" />
                    ) : (
                      <AlertTriangle className="w-4 h-4 text-[#ff8800]/60" />
                    )}
                    <span className="text-sm font-mono text-white/80 group-hover:text-white transition-colors">
                      {report.repo_full_name}
                    </span>
                    <span className="text-[10px] font-mono text-white/20 border border-white/10 px-1.5 py-0.5">
                      {report.branch}
                    </span>
                  </div>
                  <span className="text-[10px] font-mono text-white/20 flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {timeAgo(report.created_at)}
                  </span>
                </div>

                <div className="flex items-center gap-4 text-[10px] font-mono text-white/30">
                  <span className="flex items-center gap-1">
                    <GitCommit className="w-3 h-3" />
                    {report.commit_sha.slice(0, 8)}
                  </span>
                  <span className="flex items-center gap-1">
                    <FileCode className="w-3 h-3" />
                    {report.files_scanned} files
                  </span>
                  {report.commit_message && (
                    <span className="text-white/20 truncate max-w-xs">
                      {report.commit_message}
                    </span>
                  )}

                  {/* Severity pills */}
                  <div className="flex gap-2 ml-auto">
                    {report.severity_summary.critical > 0 && (
                      <span className="text-[#ff3333] bg-[#ff3333]/10 px-1.5 py-0.5">C:{report.severity_summary.critical}</span>
                    )}
                    {report.severity_summary.high > 0 && (
                      <span className="text-[#ff8800] bg-[#ff8800]/10 px-1.5 py-0.5">H:{report.severity_summary.high}</span>
                    )}
                    {report.severity_summary.medium > 0 && (
                      <span className="text-[#ffcc00] bg-[#ffcc00]/10 px-1.5 py-0.5">M:{report.severity_summary.medium}</span>
                    )}
                    {totalVulns(report) === 0 && (
                      <span className="text-[#00ff88]/60">CLEAN</span>
                    )}
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </main>
  );
}
