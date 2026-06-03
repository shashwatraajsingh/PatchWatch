"""
Manual Scan Router — for testing without GitHub webhooks.
Allows you to manually trigger a scan on any public repo+commit.
Requires authentication — scans are scoped to the logged-in user.
"""

import re
import time
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from src.database.session import get_db
from src.models.domain import ScanReport, User
from src.core.auth import get_current_user
from src.services import github_service
from src.services.scanner import scan_commit
from src.services.memory import get_previous_context, save_context, compare_with_previous, build_context_prompt
from src.services.report_generator import (
    generate_severity_summary, generate_natural_summary, generate_markdown_report,
)
from src.utils.diff_parser import parse_commit_files, prioritize_files

router = APIRouter(prefix="/scan", tags=["Manual Scan"])


def extract_repo_name(raw: str) -> str:
    """Extract 'owner/repo' from a full GitHub URL or return as-is."""
    match = re.match(r"https?://github\.com/([^/]+/[^/]+?)(?:\.git)?(?:/.*)?$", raw.strip())
    if match:
        return match.group(1)
    return raw.strip()


class ManualScanRequest(BaseModel):
    repo_full_name: str
    commit_sha: str
    branch: str = "main"


@router.post("/")
async def manual_scan(
    req: ManualScanRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Manually trigger a security scan on a specific commit.
    Requires authentication. Results are scoped to the logged-in user.
    """
    start_time = time.time()
    repo_name = extract_repo_name(req.repo_full_name)

    # 1. Fetch commit from GitHub (use user's token if available)
    commit_details = await github_service.get_commit_details(repo_name, req.commit_sha, token=user.github_token)
    if not commit_details:
        return {"status": "error", "message": "Could not fetch commit from GitHub. Check repo name and SHA."}

    commit_data = commit_details.get("commit", {})
    sha = commit_details.get("sha", req.commit_sha)
    message = commit_data.get("message", "")
    author = commit_data.get("author", {}).get("name", "unknown")

    # Check if this commit was already scanned by this user
    existing = await db.execute(
        select(ScanReport).where(ScanReport.commit_sha == sha, ScanReport.user_id == user.id)
    )
    existing_report = existing.scalar_one_or_none()
    if existing_report:
        return {
            "status": "ok",
            "message": "Commit already scanned — returning existing report.",
            "report_id": existing_report.id,
            "commit_sha": sha[:8],
            "vulnerabilities_found": len(existing_report.vulnerabilities),
            "severity_summary": existing_report.severity_summary,
            "files_scanned": existing_report.files_scanned,
            "report_markdown": existing_report.report_markdown,
        }

    # 2. Parse files
    raw_files = commit_details.get("files", [])
    parsed_files = parse_commit_files(raw_files)
    parsed_files = prioritize_files(parsed_files)

    if not parsed_files:
        return {"status": "ok", "message": "No scannable files in this commit.", "files_found": len(raw_files)}

    # 3. Load previous context
    previous = await get_previous_context(db, repo_name, req.branch, user_id=user.id)
    context_prompt = build_context_prompt(previous) if previous else None

    # 4. Run scan
    vulnerabilities = await scan_commit(parsed_files, context_prompt)

    # 5. Compare
    if previous:
        comparison = compare_with_previous(vulnerabilities, previous.get("vulnerability_fingerprints", []))
    else:
        comparison = {"new_issues": vulnerabilities, "resolved_issues": [], "recurring_issues": []}

    # 6. Generate report
    duration_ms = int((time.time() - start_time) * 1000)
    severity = generate_severity_summary(vulnerabilities)
    report_md = generate_markdown_report(
        repo_name, req.branch, sha, message,
        author, vulnerabilities, comparison, len(parsed_files), duration_ms,
    )
    summary = generate_natural_summary(repo_name, req.branch, sha, vulnerabilities, comparison)

    # 7. Save report (scoped to user)
    report = ScanReport(
        user_id=user.id,
        repo_full_name=repo_name, branch=req.branch, commit_sha=sha,
        commit_message=message, author=author,
        vulnerabilities=vulnerabilities, severity_summary=severity,
        report_markdown=report_md,
        new_issues=comparison["new_issues"],
        resolved_issues=comparison["resolved_issues"],
        recurring_issues=comparison["recurring_issues"],
        files_scanned=len(parsed_files), scan_duration_ms=duration_ms,
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)

    # 8. Update memory
    await save_context(db, repo_name, req.branch, sha, vulnerabilities, summary, user_id=user.id)

    return {
        "status": "ok",
        "report_id": report.id,
        "commit_sha": sha[:8],
        "vulnerabilities_found": len(vulnerabilities),
        "severity_summary": severity,
        "new_issues": len(comparison["new_issues"]),
        "resolved_issues": len(comparison["resolved_issues"]),
        "recurring_issues": len(comparison["recurring_issues"]),
        "files_scanned": len(parsed_files),
        "scan_duration_ms": duration_ms,
        "report_markdown": report_md,
    }
