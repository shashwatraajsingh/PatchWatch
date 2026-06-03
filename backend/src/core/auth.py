"""
Authentication utilities — JWT creation/verification and FastAPI dependency.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt, JWTError

from src.core.config import get_settings
from src.database.session import get_db
from src.models.domain import User

settings = get_settings()


def create_token(user_id: int, github_id: int, username: str) -> str:
    """Create a JWT token for a user."""
    payload = {
        "sub": str(user_id),
        "github_id": github_id,
        "username": username,
        "exp": datetime.now(timezone.utc) + timedelta(hours=settings.jwt_expiry_hours),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    """Decode and verify a JWT token."""
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    FastAPI dependency — extracts JWT from Authorization header or cookie,
    verifies it, and returns the User object.
    """
    token = None

    # Check Authorization header first
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]

    # Fall back to cookie
    if not token:
        token = request.cookies.get("patchwatch_token")

    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = decode_token(token)
        user_id = int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user


async def get_optional_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """
    Same as get_current_user but returns None instead of 401.
    Used for endpoints that work with or without auth (e.g. webhooks).
    """
    try:
        return await get_current_user(request, db)
    except HTTPException:
        return None
