from typing import Optional
from sqlalchemy.orm import Session
from app.models.models import (
    ThreatCampaign, Asset, Integration, TechniqueRiskScore, ReportSnapshot
)

class ExecutiveService:
    def compute_overview(self, db: Session) -> dict:
        total_campaigns = db.query(ThreatCampaign).count()
        total_assets = db.query(Asset).count()
        active_integrations = db.query(Integration).filter(Integration.is_active == True).count()
        total_techniques = db.query(TechniqueRiskScore).count()
        avg_risk_score = 0.0
        high_risk = 0
        latest_snapshot_date = None
        
        scores = db.query(TechniqueRiskScore).all()
        if scores:
            avg_risk_score = sum(s.overall_risk for s in scores) / len(scores)
            high_risk = sum(1 for s in scores if s.overall_risk > 0.7)
        
        latest = db.query(ReportSnapshot).order_by(ReportSnapshot.snapshot_date.desc()).first()
        if latest:
            latest_snapshot_date = latest.snapshot_date
        
        return {
            "total_campaigns": total_campaigns,
            "total_assets": total_assets,
            "active_integrations": active_integrations,
            "total_techniques": total_techniques,
            "avg_risk_score": avg_risk_score,
            "high_risk_techniques": high_risk,
            "latest_snapshot_date": latest_snapshot_date
        }

    def full_report(self, db: Session) -> dict:
        overview = self.compute_overview(db)
        # fetch additional details
        risk_snapshot = db.query(ReportSnapshot).order_by(ReportSnapshot.snapshot_date.desc()).first()
        integrations = db.query(Integration).all()
        assets = db.query(Asset).all()
        campaigns = db.query(ThreatCampaign).all()
        
        return {
            "overview": overview,
            "risk_snapshot": risk_snapshot,
            "integrations": integrations,
            "assets": assets,
            "campaigns": campaigns
        }

executive_service = ExecutiveService()