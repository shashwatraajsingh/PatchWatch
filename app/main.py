"""
PatchWatch — AI-powered security vulnerability scanner for GitHub commits.

Main FastAPI application entry point.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import init_db
from app.routers import webhook, reports, scan, repos, auth

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: create DB tables. Shutdown: cleanup."""
    print("🛡️  PatchWatch starting up...")
    await init_db()
    print("✅ Database initialized")
    print(f"📡 Webhook endpoint: POST /webhook/github")
    print(f"🔐 Auth:             GET  /auth/github")
    print(f"🔍 Manual scan:      POST /scan/")
    print(f"📄 Reports:          GET  /reports/")
    print(f"📦 Watched repos:    GET  /repos/")

    has_oauth = bool(settings.github_client_id and settings.github_client_secret)
    print(f"🔑 GitHub OAuth:     {'✅ configured' if has_oauth else '❌ not configured'}")

    has_minimax = bool(settings.minimax_api_key)
    has_qwen = bool(settings.openrouter_api_key)
    print(f"🤖 MiniMax M2.7:     {'✅ configured' if has_minimax else '❌ not configured'}")
    print(f"🤖 Qwen 3 Coder:     {'✅ configured' if has_qwen else '❌ not configured'}")

    if not has_minimax and not has_qwen:
        print("⚠️  WARNING: No AI models configured! Set MINIMAX_API_KEY or OPENROUTER_API_KEY in .env")

    yield
    print("🛡️  PatchWatch shutting down.")


app = FastAPI(
    title="PatchWatch",
    description="AI-powered security vulnerability scanner for GitHub commits. "
                "Analyzes every push, finds vulnerabilities, and tracks them across commits.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow all for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router)
app.include_router(webhook.router)
app.include_router(reports.router)
app.include_router(scan.router)
app.include_router(repos.router)


@app.get("/", tags=["Health"])
async def root():
    return {
        "service": "PatchWatch",
        "version": "1.0.0",
        "status": "running",
        "description": "AI-powered security vulnerability scanner for GitHub commits",
        "endpoints": {
            "auth_login": "GET /auth/github",
            "auth_callback": "POST /auth/github/callback",
            "auth_me": "GET /auth/me",
            "webhook": "POST /webhook/github",
            "manual_scan": "POST /scan/",
            "reports": "GET /reports/",
            "watched_repos": "GET /repos/",
            "docs": "GET /docs",
        },
    }


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "healthy"}
