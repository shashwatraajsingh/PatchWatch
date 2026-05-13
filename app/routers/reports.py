"""
Reports Router — API endpoints to retrieve scan reports.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.database import get_db
from app.models import ScanReport
from app.schemas import ScanReportResponse, ScanReportListItem

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/", response_model=list[ScanReportListItem])
async def list_reports(
    repo: Optional[str] = Query(None, description="Filter by repo (e.g. 'user/repo')"),
    branch: Optional[str] = Query(None, description="Filter by branch"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List scan reports with optional filtering."""
    stmt = select(ScanReport).order_by(desc(ScanReport.created_at))

    if repo:
        stmt = stmt.where(ScanReport.repo_full_name == repo)
    if branch:
        stmt = stmt.where(ScanReport.branch == branch)

    stmt = stmt.offset(offset).limit(limit)
    result = await db.execute(stmt)
    reports = result.scalars().all()

    return reports


@router.get("/{report_id}", response_model=ScanReportResponse)
async def get_report(report_id: int, db: AsyncSession = Depends(get_db)):
    """Get a full scan report by ID."""
    stmt = select(ScanReport).where(ScanReport.id == report_id)
    result = await db.execute(stmt)
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    return report


@router.get("/{report_id}/markdown")
async def get_report_markdown(report_id: int, db: AsyncSession = Depends(get_db)):
    """Get just the markdown report for a scan."""
    stmt = select(ScanReport).where(ScanReport.id == report_id)
    result = await db.execute(stmt)
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    return {"markdown": report.report_markdown}


@router.get("/commit/{commit_sha}", response_model=ScanReportResponse)
async def get_report_by_commit(commit_sha: str, db: AsyncSession = Depends(get_db)):
    """Get a scan report by commit SHA."""
    stmt = select(ScanReport).where(ScanReport.commit_sha == commit_sha)
    result = await db.execute(stmt)
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(status_code=404, detail="No report found for this commit")

    return report
