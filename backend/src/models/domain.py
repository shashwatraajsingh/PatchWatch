"""
SQLAlchemy models for PatchWatch.

- User: GitHub OAuth authenticated user
- ScanReport: stores every commit scan result
- CommitMemory: stores condensed context from each commit for cross-commit comparison
- WatchedRepo: repos registered for automatic webhook scanning
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey
from src.database.session import Base


class User(Base):
    """GitHub-authenticated user."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    github_id = Column(Integer, nullable=False, unique=True, index=True)
    username = Column(String(255), nullable=False, unique=True)
    email = Column(String(255), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    github_token = Column(String(500), nullable=True)  # encrypted in production

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_login = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))


class ScanReport(Base):
    """Full vulnerability report for a single commit."""

    __tablename__ = "scan_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    repo_full_name = Column(String(255), nullable=False, index=True)
    branch = Column(String(255), nullable=False)
    commit_sha = Column(String(40), nullable=False, unique=True)
    commit_message = Column(Text, nullable=True)
    author = Column(String(255), nullable=True)

    # Scan results
    vulnerabilities = Column(JSON, nullable=False, default=list)
    severity_summary = Column(JSON, nullable=False, default=dict)
    report_markdown = Column(Text, nullable=False, default="")

    # Comparison with previous commit
    new_issues = Column(JSON, nullable=False, default=list)
    resolved_issues = Column(JSON, nullable=False, default=list)
    recurring_issues = Column(JSON, nullable=False, default=list)

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
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    repo_full_name = Column(String(255), nullable=False, index=True)
    branch = Column(String(255), nullable=False)
    commit_sha = Column(String(40), nullable=False)

    vulnerability_fingerprints = Column(JSON, nullable=False, default=list)
    summary = Column(Text, nullable=False, default="")

    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))


class WatchedRepo(Base):
    """
    A repository registered for automatic webhook-based scanning.
    Each repo gets its own webhook secret for signature verification.
    """

    __tablename__ = "watched_repos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    repo_full_name = Column(String(255), nullable=False, unique=True, index=True)
    webhook_secret = Column(String(255), nullable=False)
    branches = Column(JSON, nullable=False, default=["main"])
    enabled = Column(Integer, nullable=False, default=1)
    total_scans = Column(Integer, default=0)
    last_scan_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
