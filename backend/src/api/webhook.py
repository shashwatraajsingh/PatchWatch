"""
Webhook Router — receives GitHub push events and triggers the scan pipeline.
Now validates per-repo webhook secrets from the WatchedRepo table.
"""

import hmac
import hashlib
import time
from datetime import datetime, timezone
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from sqlalchemy import select

from src.core.config import get_settings
from src.models.domain import ScanReport, WatchedRepo
from src.models.schemas import WebhookResponse
from src.services import github_service
from src.services.scanner import scan_commit
from src.services.memory import get_previous_context, save_context, compare_with_previous, build_context_prompt
from src.services.report_generator import (
    generate_severity_summary, generate_natural_summary, generate_markdown_report,
)
from src.utils.diff_parser import parse_commit_files, prioritize_files

router = APIRouter(prefix="/webhook", tags=["Webhook"])
settings = get_settings()


def verify_signature(payload_body: bytes, signature: str, secret: str) -> bool:
    """Verify GitHub webhook HMAC-SHA256 signature against a given secret."""
    if not secret:
        return True

    if not signature or not signature.startswith("sha256="):
        return False

    expected = hmac.new(secret.encode(), payload_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)


async def _run_scan_pipeline(payload: dict, repo_full_name: str):
    """The full scan pipeline — runs as a background task with its own DB session."""
    from src.database.session import async_session

    async with async_session() as db:
        start_time = time.time()

        commit_info = github_service.parse_push_webhook(payload)
        if not commit_info:
            print("[Pipeline] Skipped: no actionable commit data")
            return

        repo = commit_info["repo_full_name"]
        branch = commit_info["branch"]
        sha = commit_info["commit_sha"]

        # Check if this branch should be scanned
        watched = await db.execute(
            select(WatchedRepo).where(WatchedRepo.repo_full_name == repo)
        )
        watched_repo = watched.scalar_one_or_none()

        if watched_repo:
            allowed_branches = watched_repo.branches or ["main"]
            if branch not in allowed_branches and "*" not in allowed_branches:
                print(f"[Pipeline] Skipped: branch '{branch}' not in watched list {allowed_branches}")
                return

        print(f"[Pipeline] 🔍 Auto-scanning {repo}@{branch} commit {sha[:8]}...")

        # Check for duplicate
        existing = await db.execute(select(ScanReport).where(ScanReport.commit_sha == sha))
        if existing.scalar_one_or_none():
            print(f"[Pipeline] Skipped: commit {sha[:8]} already scanned")
            return

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
            # Update watched repo stats
            if watched_repo:
                watched_repo.total_scans = (watched_repo.total_scans or 0) + 1
                watched_repo.last_scan_at = datetime.now(timezone.utc)
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

        # 7. Save report
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

        # 8. Update memory
        await save_context(db, repo, branch, sha, vulnerabilities, summary)

        # 9. Update watched repo stats
        if watched_repo:
            watched_repo.total_scans = (watched_repo.total_scans or 0) + 1
            watched_repo.last_scan_at = datetime.now(timezone.utc)
            await db.commit()

        print(f"[Pipeline] ✅ Scan complete for {sha[:8]}: {len(vulnerabilities)} issue(s) found in {duration_ms}ms")


@router.post("/github", response_model=WebhookResponse)
async def github_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    GitHub push webhook endpoint.
    Looks up the repo in WatchedRepos to validate the per-repo webhook secret.
    If not registered, falls back to the global GITHUB_WEBHOOK_SECRET.
    """
    body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256", "")
    event = request.headers.get("X-GitHub-Event", "")

    if event == "ping":
        return WebhookResponse(status="ok", message="Pong! PatchWatch is listening.")

    if event != "push":
        return WebhookResponse(status="skipped", message=f"Ignoring event: {event}")

    payload = await request.json()

    # Extract repo name from payload
    repo_full_name = payload.get("repository", {}).get("full_name", "")

    # Try to find this repo in watched repos for per-repo secret
    from src.database.session import async_session
    async with async_session() as db:
        result = await db.execute(
            select(WatchedRepo).where(WatchedRepo.repo_full_name == repo_full_name)
        )
        watched_repo = result.scalar_one_or_none()

    if watched_repo:
        # Registered repo — validate with per-repo secret
        if not watched_repo.enabled:
            return WebhookResponse(status="skipped", message="Repository scanning is paused.")

        if not verify_signature(body, signature, watched_repo.webhook_secret):
            raise HTTPException(status_code=401, detail="Invalid webhook signature for this repository")
    else:
        # Not registered — fall back to global secret (for backward compat)
        global_secret = settings.github_webhook_secret
        if global_secret and not global_secret.startswith("your_"):
            if not verify_signature(body, signature, global_secret):
                raise HTTPException(status_code=401, detail="Invalid webhook signature")

    # Kick off scan in background
    background_tasks.add_task(_run_scan_pipeline, payload, repo_full_name)

    commit_sha = payload.get("head_commit", {}).get("id", "unknown")
    return WebhookResponse(
        status="accepted",
        message=f"Scan queued for {repo_full_name} commit {commit_sha[:8]}",
    )
