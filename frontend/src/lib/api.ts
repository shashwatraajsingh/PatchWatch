const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface Vulnerability {
  id: string;
  severity: "critical" | "high" | "medium" | "low" | "info";
  category: string;
  file: string;
  line: number | null;
  description: string;
  recommendation: string;
  code_snippet: string | null;
}

export interface SeveritySummary {
  critical: number;
  high: number;
  medium: number;
  low: number;
  info: number;
}

export interface ScanReport {
  id: number;
  repo_full_name: string;
  branch: string;
  commit_sha: string;
  commit_message: string | null;
  author: string | null;
  vulnerabilities: Vulnerability[];
  severity_summary: SeveritySummary;
  report_markdown: string;
  new_issues: Vulnerability[];
  resolved_issues: Vulnerability[];
  recurring_issues: Vulnerability[];
  files_scanned: number;
  scan_duration_ms: number;
  created_at: string;
}

export interface ScanReportListItem {
  id: number;
  repo_full_name: string;
  branch: string;
  commit_sha: string;
  commit_message: string | null;
  author: string | null;
  severity_summary: SeveritySummary;
  files_scanned: number;
  created_at: string;
}

export interface ManualScanRequest {
  repo_full_name: string;
  commit_sha: string;
  branch: string;
}

export interface ManualScanResponse {
  status: string;
  message?: string;
  report_id?: number;
  commit_sha?: string;
  vulnerabilities_found?: number;
  severity_summary?: SeveritySummary;
  new_issues?: number;
  resolved_issues?: number;
  recurring_issues?: number;
  files_scanned?: number;
  scan_duration_ms?: number;
  report_markdown?: string;
}

export async function fetchReports(repo?: string, branch?: string): Promise<ScanReportListItem[]> {
  const params = new URLSearchParams();
  if (repo) params.set("repo", repo);
  if (branch) params.set("branch", branch);
  const res = await fetch(`${API_BASE}/reports/?${params.toString()}`);
  if (!res.ok) throw new Error("Failed to fetch reports");
  return res.json();
}

export async function fetchReport(id: number): Promise<ScanReport> {
  const res = await fetch(`${API_BASE}/reports/${id}`);
  if (!res.ok) throw new Error("Report not found");
  return res.json();
}

export async function triggerScan(req: ManualScanRequest): Promise<ManualScanResponse> {
  const res = await fetch(`${API_BASE}/scan/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!res.ok) throw new Error("Scan failed");
  return res.json();
}

export async function fetchHealth(): Promise<{ status: string }> {
  const res = await fetch(`${API_BASE}/health`);
  return res.json();
}

// ── Watched Repos ─────────────────────────────────────────────

export interface WatchedRepo {
  id: number;
  repo_full_name: string;
  webhook_secret: string;
  webhook_url: string;
  branches: string[];
  enabled: boolean;
  total_scans: number;
  last_scan_at: string | null;
  created_at: string;
}

export async function fetchWatchedRepos(): Promise<WatchedRepo[]> {
  const res = await fetch(`${API_BASE}/repos/`);
  if (!res.ok) throw new Error("Failed to fetch repos");
  return res.json();
}

export async function addWatchedRepo(repo_full_name: string, branches: string[] = ["main"]): Promise<WatchedRepo> {
  const res = await fetch(`${API_BASE}/repos/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ repo_full_name, branches }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to add repo");
  }
  return res.json();
}

export async function toggleRepo(id: number, enabled: boolean): Promise<WatchedRepo> {
  const res = await fetch(`${API_BASE}/repos/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ enabled }),
  });
  if (!res.ok) throw new Error("Failed to update repo");
  return res.json();
}

export async function deleteRepo(id: number): Promise<void> {
  const res = await fetch(`${API_BASE}/repos/${id}`, { method: "DELETE" });
  if (!res.ok) throw new Error("Failed to delete repo");
}

export async function regenerateSecret(id: number): Promise<WatchedRepo> {
  const res = await fetch(`${API_BASE}/repos/${id}/regenerate-secret`, { method: "POST" });
  if (!res.ok) throw new Error("Failed to regenerate secret");
  return res.json();
}
