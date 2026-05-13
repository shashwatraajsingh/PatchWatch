"""
Pydantic schemas for request/response validation.
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# ── Vulnerability ──────────────────────────────────────────────

class Vulnerability(BaseModel):
    id: str                          # unique fingerprint e.g. "sql-injection-auth.py-42"
    severity: str                    # critical | high | medium | low | info
    category: str                    # e.g. "SQL Injection", "Hardcoded Secret"
    file: str
    line: Optional[int] = None
    description: str
    recommendation: str
    code_snippet: Optional[str] = None


# ── Report Response ────────────────────────────────────────────

class SeveritySummary(BaseModel):
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    info: int = 0


class ScanReportResponse(BaseModel):
    id: int
    repo_full_name: str
    branch: str
    commit_sha: str
    commit_message: Optional[str]
    author: Optional[str]

    vulnerabilities: list[Vulnerability]
    severity_summary: SeveritySummary
    report_markdown: str

    new_issues: list[Vulnerability]
    resolved_issues: list[Vulnerability]
    recurring_issues: list[Vulnerability]

    files_scanned: int
    scan_duration_ms: int
    created_at: datetime

    model_config = {"from_attributes": True}


class ScanReportListItem(BaseModel):
    id: int
    repo_full_name: str
    branch: str
    commit_sha: str
    commit_message: Optional[str]
    author: Optional[str]
    severity_summary: SeveritySummary
    files_scanned: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Webhook ────────────────────────────────────────────────────

class WebhookResponse(BaseModel):
    status: str
    message: str
    report_id: Optional[int] = None
