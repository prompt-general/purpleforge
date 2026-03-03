from typing import Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.executive import executive_service
from app.schemas.schemas import ExecutiveOverviewResponse, ExecutiveReportResponse

router = APIRouter()

@router.get("/overview", response_model=ExecutiveOverviewResponse)
def get_overview(db: Session = Depends(get_db)) -> Any:
    """Return high-level metrics for executive dashboard."""
    overview = executive_service.compute_overview(db)
    return overview

@router.get("/report", response_model=ExecutiveReportResponse)
def get_full_report(db: Session = Depends(get_db)) -> Any:
    """Return detailed executive report including snapshots and entities."""
    report = executive_service.full_report(db)
    return report
