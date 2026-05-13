"""
GitHub Service — fetches commit data, diffs, and file changes via the GitHub API.
Handles webhook payload parsing.
"""

import httpx
from typing import Optional
from app.config import get_settings

settings = get_settings()

GITHUB_API = "https://api.github.com"


def _headers() -> dict:
    """Auth headers for GitHub API requests."""
    h = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "PatchWatch/1.0",
    }
    if settings.github_token and not settings.github_token.startswith("your_"):
        h["Authorization"] = f"Bearer {settings.github_token}"
    return h


async def get_commit_details(repo_full_name: str, commit_sha: str) -> Optional[dict]:
    """
    Fetch full commit details including file patches from GitHub API.
    GET /repos/{owner}/{repo}/commits/{sha}
    """
    url = f"{GITHUB_API}/repos/{repo_full_name}/commits/{commit_sha}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(url, headers=_headers())

        if resp.status_code != 200:
            print(f"[GitHub] Failed to fetch commit {commit_sha}: {resp.status_code}")
            print(f"[GitHub] Response: {resp.text[:500]}")
            return None

        return resp.json()


async def get_commit_diff(repo_full_name: str, commit_sha: str) -> Optional[str]:
    """
    Fetch the raw diff of a commit.
    Uses Accept: application/vnd.github.v3.diff header.
    """
    url = f"{GITHUB_API}/repos/{repo_full_name}/commits/{commit_sha}"
    headers = _headers()
    headers["Accept"] = "application/vnd.github.v3.diff"

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(url, headers=headers)

        if resp.status_code != 200:
            return None

        return resp.text


def parse_push_webhook(payload: dict) -> Optional[dict]:
    """
    Extract relevant info from a GitHub push webhook payload.
    Returns None if the push should be skipped (e.g. branch deletion).
    """
    # Skip branch deletions
    if payload.get("deleted", False):
        return None

    # Skip if no commits
    commits = payload.get("commits", [])
    if not commits:
        return None

    ref = payload.get("ref", "")
    branch = ref.replace("refs/heads/", "") if ref.startswith("refs/heads/") else ref

    repo = payload.get("repository", {})
    repo_full_name = repo.get("full_name", "")

    # Get the head commit (most recent)
    head_commit = payload.get("head_commit") or commits[-1]

    return {
        "repo_full_name": repo_full_name,
        "branch": branch,
        "commit_sha": head_commit.get("id", ""),
        "commit_message": head_commit.get("message", ""),
        "author": head_commit.get("author", {}).get("name", "unknown"),
        "timestamp": head_commit.get("timestamp", ""),
        "added": head_commit.get("added", []),
        "modified": head_commit.get("modified", []),
        "removed": head_commit.get("removed", []),
    }
