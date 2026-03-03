from typing import Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.models import Report
from app.schemas.schemas import ReportCreate, ReportResponse
from app.services.reports import generate_coverage_report

router = APIRouter()

@router.post("/", response_model=ReportResponse, status_code=201)
def create_report(
    *,
    db: Session = Depends(get_db),
    report_in: ReportCreate
) -> Any:
    """
    Generate a new coverage report.
    Snapshots current validation results and calculates detection coverage percentage.
    """
    report = generate_coverage_report(db, name=report_in.name)
    return report

@router.get("/", response_model=List[ReportResponse])
def list_reports(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    List all historically generated coverage reports.
    """
    reports = db.query(Report).offset(skip).limit(limit).all()
    return reports
