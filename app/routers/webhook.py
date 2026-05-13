"""
Webhook Router — receives GitHub push events and triggers the scan pipeline.
"""

import hmac
import hashlib
import time
from fastapi import APIRouter, Request, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models import ScanReport
from app.schemas import WebhookResponse
from app.services import github_service
from app.services.scanner import scan_commit
from app.services.memory import get_previous_context, save_context, compare_with_previous, build_context_prompt
from app.services.report_generator import (
    generate_severity_summary, generate_natural_summary, generate_markdown_report,
)
from app.utils.diff_parser import parse_commit_files, prioritize_files

router = APIRouter(prefix="/webhook", tags=["Webhook"])
settings = get_settings()


def verify_signature(payload_body: bytes, signature: str) -> bool:
    """Verify GitHub webhook HMAC-SHA256 signature."""
    if not settings.github_webhook_secret:
        return True  # skip verification if no secret configured

    if not signature or not signature.startswith("sha256="):
        return False

    expected = hmac.new(
        settings.github_webhook_secret.encode(),
        payload_body,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(f"sha256={expected}", signature)


async def _run_scan_pipeline(payload: dict, db: AsyncSession):
    """The full scan pipeline — runs as a background task."""
    start_time = time.time()

    commit_info = github_service.parse_push_webhook(payload)
    if not commit_info:
        print("[Pipeline] Skipped: no actionable commit data")
        return

    repo = commit_info["repo_full_name"]
    branch = commit_info["branch"]
    sha = commit_info["commit_sha"]

    print(f"[Pipeline] Scanning {repo}@{branch} commit {sha[:8]}...")

    # 1. Fetch full commit details from GitHub API
    commit_details = await github_service.get_commit_details(repo, sha)
    if not commit_details:
        print(f"[Pipeline] Failed to fetch commit details for {sha}")
        return

    # 2. Parse and filter files
    raw_files = commit_details.get("files", [])
    parsed_files = parse_commit_files(raw_files)
    parsed_files = prioritize_files(parsed_files)

    if not parsed_files:
        print(f"[Pipeline] No scannable files in commit {sha[:8]}")
        # Still save a clean report
        comparison = {"new_issues": [], "resolved_issues": [], "recurring_issues": []}
        report_md = generate_markdown_report(
            repo, branch, sha, commit_info["commit_message"],
            commit_info["author"], [], comparison, 0,
            int((time.time() - start_time) * 1000),
        )
        report = ScanReport(
            repo_full_name=repo, branch=branch, commit_sha=sha,
            commit_message=commit_info["commit_message"], author=commit_info["author"],
            vulnerabilities=[], severity_summary={"critical":0,"high":0,"medium":0,"low":0,"info":0},
            report_markdown=report_md, new_issues=[], resolved_issues=[], recurring_issues=[],
            files_scanned=0, scan_duration_ms=int((time.time() - start_time) * 1000),
        )
        db.add(report)
        await db.commit()
        return

    # 3. Load previous context from memory
    previous = await get_previous_context(db, repo, branch)
    context_prompt = build_context_prompt(previous) if previous else None

    # 4. Run AI security scan
    print(f"[Pipeline] Scanning {len(parsed_files)} file(s)...")
    vulnerabilities = await scan_commit(parsed_files, context_prompt)

    # 5. Compare with previous scan
    if previous:
        comparison = compare_with_previous(
            vulnerabilities, previous.get("vulnerability_fingerprints", [])
        )
    else:
        comparison = {
            "new_issues": vulnerabilities,
            "resolved_issues": [],
            "recurring_issues": [],
        }

    # 6. Generate report
    duration_ms = int((time.time() - start_time) * 1000)
    severity = generate_severity_summary(vulnerabilities)
    report_md = generate_markdown_report(
        repo, branch, sha, commit_info["commit_message"],
        commit_info["author"], vulnerabilities, comparison,
        len(parsed_files), duration_ms,
    )
    summary = generate_natural_summary(repo, branch, sha, vulnerabilities, comparison)

    # 7. Save report to database
    report = ScanReport(
        repo_full_name=repo, branch=branch, commit_sha=sha,
        commit_message=commit_info["commit_message"], author=commit_info["author"],
        vulnerabilities=[v for v in vulnerabilities],
        severity_summary=severity, report_markdown=report_md,
        new_issues=comparison["new_issues"],
        resolved_issues=comparison["resolved_issues"],
        recurring_issues=comparison["recurring_issues"],
        files_scanned=len(parsed_files), scan_duration_ms=duration_ms,
    )
    db.add(report)
    await db.commit()

    # 8. Update memory for next scan
    await save_context(db, repo, branch, sha, vulnerabilities, summary)

    print(f"[Pipeline] ✅ Scan complete for {sha[:8]}: {len(vulnerabilities)} issue(s) found in {duration_ms}ms")


@router.post("/github", response_model=WebhookResponse)
async def github_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    GitHub push webhook endpoint.
    Verifies signature, then kicks off the scan pipeline in the background.
    """
    body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256", "")

    if not verify_signature(body, signature):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    event = request.headers.get("X-GitHub-Event", "")
    if event == "ping":
        return WebhookResponse(status="ok", message="Pong! PatchWatch is listening.")

    if event != "push":
        return WebhookResponse(status="skipped", message=f"Ignoring event: {event}")

    payload = await request.json()

    # We need a fresh DB session for the background task
    from app.database import async_session
    async def run_in_background():
        async with async_session() as db:
            await _run_scan_pipeline(payload, db)

    background_tasks.add_task(run_in_background)

    commit_sha = payload.get("head_commit", {}).get("id", "unknown")
    return WebhookResponse(
        status="accepted",
        message=f"Scan queued for commit {commit_sha[:8]}",
    )
