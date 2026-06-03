"""
Memory Service — stores and retrieves commit context for cross-commit comparison.
"""

from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.domain import CommitMemory


async def get_previous_context(db: AsyncSession, repo_full_name: str, branch: str, user_id: int = None) -> Optional[dict]:
    """Load last scan context for a repo+branch, optionally scoped by user."""
    stmt = (
        select(CommitMemory)
        .where(CommitMemory.repo_full_name == repo_full_name)
        .where(CommitMemory.branch == branch)
    )
    if user_id is not None:
        stmt = stmt.where(CommitMemory.user_id == user_id)
    result = await db.execute(stmt)
    memory = result.scalar_one_or_none()

    if not memory:
        return None

    return {
        "commit_sha": memory.commit_sha,
        "summary": memory.summary,
        "vulnerability_fingerprints": memory.vulnerability_fingerprints,
    }


async def save_context(db: AsyncSession, repo_full_name: str, branch: str,
                        commit_sha: str, vulnerabilities: list[dict], summary: str,
                        user_id: int = None):
    """Upsert commit memory for a repo+branch, optionally scoped by user."""
    fingerprints = [
        {
            "id": v.get("id", ""),
            "category": v.get("category", ""),
            "file": v.get("file", ""),
            "severity": v.get("severity", ""),
            "description": v.get("description", "")[:100],
        }
        for v in vulnerabilities
    ]

    stmt = (
        select(CommitMemory)
        .where(CommitMemory.repo_full_name == repo_full_name)
        .where(CommitMemory.branch == branch)
    )
    if user_id is not None:
        stmt = stmt.where(CommitMemory.user_id == user_id)
    result = await db.execute(stmt)
    memory = result.scalar_one_or_none()

    if memory:
        memory.commit_sha = commit_sha
        memory.vulnerability_fingerprints = fingerprints
        memory.summary = summary
    else:
        memory = CommitMemory(
            user_id=user_id,
            repo_full_name=repo_full_name, branch=branch, commit_sha=commit_sha,
            vulnerability_fingerprints=fingerprints, summary=summary,
        )
        db.add(memory)

    await db.commit()


def compare_with_previous(current_vulns: list[dict], previous_fingerprints: list[dict]) -> dict:
    """Compare current vs previous findings → new, resolved, recurring."""
    prev_ids = {fp["id"] for fp in previous_fingerprints}
    curr_ids = {v.get("id", "") for v in current_vulns}
    curr_by_id = {v.get("id", ""): v for v in current_vulns}

    new_issues = [curr_by_id[vid] for vid in (curr_ids - prev_ids) if vid in curr_by_id]
    recurring_issues = [curr_by_id[vid] for vid in (curr_ids & prev_ids) if vid in curr_by_id]
    resolved_issues = [fp for fp in previous_fingerprints if fp["id"] in (prev_ids - curr_ids)]

    return {"new_issues": new_issues, "recurring_issues": recurring_issues, "resolved_issues": resolved_issues}


def build_context_prompt(previous: dict) -> str:
    """Build context string from previous scan memory for the LLM."""
    fingerprints = previous.get("vulnerability_fingerprints", [])
    if not fingerprints:
        return f"Previous commit ({previous['commit_sha'][:8]}) had no known vulnerabilities."

    issues_text = "\n".join(
        f"  - [{fp['severity'].upper()}] {fp['category']} in {fp['file']}: {fp['description']}"
        for fp in fingerprints
    )
    return (f"Previous commit ({previous['commit_sha'][:8]}) had these known issues:\n{issues_text}\n\n"
            f"Summary: {previous.get('summary', 'N/A')}\n\n"
            f"Flag any still present as RECURRING, any new ones as NEW.")
