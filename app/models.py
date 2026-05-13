"""
SQLAlchemy models for PatchWatch.

- ScanReport: stores every commit scan result
- CommitMemory: stores condensed context from each commit for cross-commit comparison
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from app.database import Base


class ScanReport(Base):
    """Full vulnerability report for a single commit."""

    __tablename__ = "scan_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    repo_full_name = Column(String(255), nullable=False, index=True)   # e.g. "user/repo"
    branch = Column(String(255), nullable=False)
    commit_sha = Column(String(40), nullable=False, unique=True)
    commit_message = Column(Text, nullable=True)
    author = Column(String(255), nullable=True)

    # Scan results
    vulnerabilities = Column(JSON, nullable=False, default=list)       # list of vuln dicts
    severity_summary = Column(JSON, nullable=False, default=dict)      # {"critical":0,"high":1,...}
    report_markdown = Column(Text, nullable=False, default="")         # full markdown report

    # Comparison with previous commit
    new_issues = Column(JSON, nullable=False, default=list)            # issues introduced in this commit
    resolved_issues = Column(JSON, nullable=False, default=list)       # issues from last commit now gone
    recurring_issues = Column(JSON, nullable=False, default=list)      # still present from last commit

    files_scanned = Column(Integer, default=0)
    scan_duration_ms = Column(Integer, default=0)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class CommitMemory(Base):
    """
    Condensed memory of the last scanned commit per repo+branch.
    Used to diff against the next commit's findings.
    """

    __tablename__ = "commit_memory"

    id = Column(Integer, primary_key=True, autoincrement=True)
    repo_full_name = Column(String(255), nullable=False, index=True)
    branch = Column(String(255), nullable=False)
    commit_sha = Column(String(40), nullable=False)

    # Condensed context for the LLM to compare against
    vulnerability_fingerprints = Column(JSON, nullable=False, default=list)  # list of issue hashes/summaries
    summary = Column(Text, nullable=False, default="")                       # natural language summary

    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))


class WatchedRepo(Base):
    """
    A repository registered for automatic webhook-based scanning.
    Each repo gets its own webhook secret for signature verification.
    """

    __tablename__ = "watched_repos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    repo_full_name = Column(String(255), nullable=False, unique=True, index=True)  # e.g. "user/repo"
    webhook_secret = Column(String(255), nullable=False)          # per-repo HMAC secret
    branches = Column(JSON, nullable=False, default=["main"])     # branches to scan
    enabled = Column(Integer, nullable=False, default=1)          # 1=active, 0=paused
    total_scans = Column(Integer, default=0)
    last_scan_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

