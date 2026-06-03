"""
Auth Router — GitHub OAuth login flow.

1. /auth/github → redirects user to GitHub's OAuth page
2. /auth/github/callback → GitHub redirects back here with a code
3. We exchange code for token → fetch user profile → create/update user → return JWT
"""

import httpx
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import get_settings
from src.database.session import get_db
from src.models.domain import User
from src.core.auth import create_token, get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])
settings = get_settings()

GITHUB_AUTH_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_URL = "https://api.github.com/user"


@router.get("/github")
async def github_login():
    """Redirect to GitHub OAuth authorization page."""
    if not settings.github_client_id:
        raise HTTPException(status_code=500, detail="GitHub OAuth not configured. Set GITHUB_CLIENT_ID in .env")

    params = {
        "client_id": settings.github_client_id,
        "redirect_uri": f"{settings.frontend_url}/auth/callback",
        "scope": "repo user:email",
    }
    url = f"{GITHUB_AUTH_URL}?{'&'.join(f'{k}={v}' for k, v in params.items())}"
    return RedirectResponse(url=url)


@router.post("/github/callback")
async def github_callback(code: str, db: AsyncSession = Depends(get_db)):
    """
    Exchange GitHub OAuth code for access token, fetch user profile,
    create/update user in DB, and return a JWT.
    """
    if not settings.github_client_id or not settings.github_client_secret:
        raise HTTPException(status_code=500, detail="GitHub OAuth not configured")

    # 1. Exchange code for access token
    async with httpx.AsyncClient() as client:
        token_res = await client.post(
            GITHUB_TOKEN_URL,
            json={
                "client_id": settings.github_client_id,
                "client_secret": settings.github_client_secret,
                "code": code,
            },
            headers={"Accept": "application/json"},
        )

    if token_res.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to exchange code for token")

    token_data = token_res.json()
    access_token = token_data.get("access_token")

    if not access_token:
        error = token_data.get("error_description", "Unknown error")
        raise HTTPException(status_code=400, detail=f"GitHub OAuth error: {error}")

    # 2. Fetch user profile from GitHub
    async with httpx.AsyncClient() as client:
        user_res = await client.get(
            GITHUB_USER_URL,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
            },
        )

    if user_res.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to fetch GitHub user profile")

    gh_user = user_res.json()
    github_id = gh_user["id"]
    username = gh_user["login"]
    email = gh_user.get("email")
    avatar_url = gh_user.get("avatar_url")

    # 3. Create or update user
    result = await db.execute(select(User).where(User.github_id == github_id))
    user = result.scalar_one_or_none()

    if user:
        # Update existing user
        user.username = username
        user.email = email
        user.avatar_url = avatar_url
        user.github_token = access_token
        user.last_login = datetime.now(timezone.utc)
    else:
        # Create new user
        user = User(
            github_id=github_id,
            username=username,
            email=email,
            avatar_url=avatar_url,
            github_token=access_token,
        )
        db.add(user)

    await db.commit()
    await db.refresh(user)

    # 4. Generate JWT
    token = create_token(user.id, user.github_id, user.username)

    return {
        "token": token,
        "user": {
            "id": user.id,
            "username": user.username,
            "avatar_url": user.avatar_url,
            "github_id": user.github_id,
        },
    }


@router.get("/me")
async def get_me(user: User = Depends(get_current_user)):
    """Return the currently authenticated user."""
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "avatar_url": user.avatar_url,
        "github_id": user.github_id,
    }
