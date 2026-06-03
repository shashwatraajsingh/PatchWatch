"""
Repos Router — manage repositories registered for automatic webhook scanning.
All operations are scoped to the authenticated user.
"""

import secrets
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional

from src.database.session import get_db
from src.models.domain import WatchedRepo, User
from src.core.auth import get_current_user
from src.core.config import get_settings

router = APIRouter(prefix="/repos", tags=["Watched Repos"])
settings = get_settings()


class AddRepoRequest(BaseModel):
    repo_full_name: str
    branches: list[str] = ["main"]


class UpdateRepoRequest(BaseModel):
    branches: Optional[list[str]] = None
    enabled: Optional[bool] = None


class WatchedRepoResponse(BaseModel):
    id: int
    repo_full_name: str
    webhook_secret: str
    webhook_url: str
    branches: list[str]
    enabled: bool
    total_scans: int
    last_scan_at: Optional[str]
    created_at: str


def _to_response(repo: WatchedRepo) -> dict:
    if settings.backend_url:
        webhook_url = f"{settings.backend_url.rstrip('/')}/webhook/github"
    else:
        webhook_url = f"http://{settings.host}:{settings.port}/webhook/github"

    return {
        "id": repo.id,
        "repo_full_name": repo.repo_full_name,
        "webhook_secret": repo.webhook_secret,
        "webhook_url": webhook_url,
        "branches": repo.branches or ["main"],
        "enabled": bool(repo.enabled),
        "total_scans": repo.total_scans or 0,
        "last_scan_at": repo.last_scan_at.isoformat() if repo.last_scan_at else None,
        "created_at": repo.created_at.isoformat() if repo.created_at else "",
    }


@router.get("/")
async def list_repos(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List watched repositories for the authenticated user."""
    stmt = select(WatchedRepo).where(
        WatchedRepo.user_id == user.id
    ).order_by(WatchedRepo.created_at.desc())
    result = await db.execute(stmt)
    repos = result.scalars().all()
    return [_to_response(r) for r in repos]


@router.post("/")
async def add_repo(
    req: AddRepoRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Register a repository for automatic webhook scanning."""
    existing = await db.execute(
        select(WatchedRepo).where(
            WatchedRepo.repo_full_name == req.repo_full_name,
            WatchedRepo.user_id == user.id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Repository already registered")

    webhook_secret = secrets.token_hex(32)

    repo = WatchedRepo(
        user_id=user.id,
        repo_full_name=req.repo_full_name,
        webhook_secret=webhook_secret,
        branches=req.branches,
        enabled=1,
    )
    db.add(repo)
    await db.commit()
    await db.refresh(repo)

    return _to_response(repo)


@router.get("/{repo_id}")
async def get_repo(
    repo_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get a watched repository by ID."""
    stmt = select(WatchedRepo).where(WatchedRepo.id == repo_id, WatchedRepo.user_id == user.id)
    result = await db.execute(stmt)
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    return _to_response(repo)


@router.patch("/{repo_id}")
async def update_repo(
    repo_id: int,
    req: UpdateRepoRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Update a watched repository (branches, enabled/disabled)."""
    stmt = select(WatchedRepo).where(WatchedRepo.id == repo_id, WatchedRepo.user_id == user.id)
    result = await db.execute(stmt)
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    if req.branches is not None:
        repo.branches = req.branches
    if req.enabled is not None:
        repo.enabled = 1 if req.enabled else 0

    await db.commit()
    await db.refresh(repo)
    return _to_response(repo)


@router.delete("/{repo_id}")
async def remove_repo(
    repo_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Unregister a repository from automatic scanning."""
    stmt = select(WatchedRepo).where(WatchedRepo.id == repo_id, WatchedRepo.user_id == user.id)
    result = await db.execute(stmt)
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    await db.delete(repo)
    await db.commit()
    return {"status": "ok", "message": f"Removed {repo.repo_full_name} from watched repos"}


@router.post("/{repo_id}/regenerate-secret")
async def regenerate_secret(
    repo_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Regenerate the webhook secret for a repository."""
    stmt = select(WatchedRepo).where(WatchedRepo.id == repo_id, WatchedRepo.user_id == user.id)
    result = await db.execute(stmt)
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    repo.webhook_secret = secrets.token_hex(32)
    await db.commit()
    await db.refresh(repo)
    return _to_response(repo)
