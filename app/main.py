"""
PatchWatch — AI-powered security vulnerability scanner for GitHub commits.

Main FastAPI application entry point.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import init_db
from app.routers import webhook, reports, scan

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: create DB tables. Shutdown: cleanup."""
    print("🛡️  PatchWatch starting up...")
    await init_db()
    print("✅ Database initialized")
    print(f"📡 Webhook endpoint: POST /webhook/github")
    print(f"🔍 Manual scan:      POST /scan/")
    print(f"📄 Reports:          GET  /reports/")

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
app.include_router(webhook.router)
app.include_router(reports.router)
app.include_router(scan.router)


@app.get("/", tags=["Health"])
async def root():
    return {
        "service": "PatchWatch",
        "version": "1.0.0",
        "status": "running",
        "description": "AI-powered security vulnerability scanner for GitHub commits",
        "endpoints": {
            "webhook": "POST /webhook/github",
            "manual_scan": "POST /scan/",
            "reports": "GET /reports/",
            "report_detail": "GET /reports/{id}",
            "report_markdown": "GET /reports/{id}/markdown",
            "docs": "GET /docs",
        },
    }


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "healthy"}
