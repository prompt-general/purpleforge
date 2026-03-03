import logging
from typing import Dict, List, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.models import (
    TechniqueRiskScore, ReportSnapshot, CampaignTechnique,
    Execution, ValidationResult
)

logger = logging.getLogger(__name__)

class RiskScoringEngine:
    """Risk scoring engine for attack techniques.
    
    Formula: Risk = Likelihood × Impact × Detection Gap
    
    Likelihood: frequency of technique in campaigns (0.0-1.0)
    Impact: criticality/blast radius (0.0-1.0) - default 0.5, can be configured per environment
    Detection Gap: 1.0 - detection_coverage_rate
    """

    def calculate_likelihood(self, db: Session, mitre_id: str) -> float:
        """Calculate likelihood as frequency of technique in campaigns."""
        total_techniques = db.query(CampaignTechnique).count()
        if total_techniques == 0:
            return 0.0
        
        technique_count = db.query(CampaignTechnique).filter(
            CampaignTechnique.mitre_id == mitre_id
        ).count()
        
        return min(float(technique_count) / total_techniques, 1.0)

    def calculate_detection_coverage(self, db: Session, mitre_id: str) -> float:
        """Calculate detection coverage rate: detections / total executions."""
        executions = db.query(Execution).join(
            Execution.technique
        ).filter(
            Execution.technique.mitre_id == mitre_id
        ).all()
        
        if not executions:
            return 0.0
        
        detected = 0
        for execution in executions:
            validation = db.query(ValidationResult).filter(
                ValidationResult.execution_id == execution.id,
                ValidationResult.is_detected == "TRUE"
            ).first()
            if validation:
                detected += 1
        
        return float(detected) / len(executions) if executions else 0.0

    def calculate_risk_score(
        self,
        db: Session,
        mitre_id: str,
        technique_name: str = None,
        impact: float = 0.5
    ) -> TechniqueRiskScore:
        """Calculate and persist risk score for a technique."""
        likelihood = self.calculate_likelihood(db, mitre_id)
        detection_coverage = self.calculate_detection_coverage(db, mitre_id)
        detection_gap = 1.0 - detection_coverage
        overall_risk = likelihood * impact * detection_gap
        
        # Upsert risk score
        existing = db.query(TechniqueRiskScore).filter(
            TechniqueRiskScore.mitre_id == mitre_id
        ).first()
        
        if existing:
            existing.likelihood = likelihood
            existing.impact = impact
            existing.detection_coverage = detection_coverage
            existing.detection_gap = detection_gap
            existing.overall_risk = overall_risk
            existing.calculated_at = datetime.utcnow()
            if technique_name:
                existing.technique_name = technique_name
        else:
            existing = TechniqueRiskScore(
                mitre_id=mitre_id,
                technique_name=technique_name,
                likelihood=likelihood,
                impact=impact,
                detection_coverage=detection_coverage,
                detection_gap=detection_gap,
                overall_risk=overall_risk
            )
            db.add(existing)
        
        db.commit()
        db.refresh(existing)
        return existing

    def generate_risk_snapshot(self, db: Session) -> ReportSnapshot:
        """Generate a snapshot of all technique risk scores."""
        risk_scores = db.query(TechniqueRiskScore).all()
        
        if not risk_scores:
            # No techniques yet; create an empty snapshot
            snapshot = ReportSnapshot(
                total_techniques=0,
                avg_risk_score=0.0,
                high_risk_count=0,
                detection_gap_avg=0.0,
                details={}
            )
            db.add(snapshot)
            db.commit()
            db.refresh(snapshot)
            return snapshot
        
        avg_risk = sum(score.overall_risk for score in risk_scores) / len(risk_scores)
        high_risk_count = sum(1 for score in risk_scores if score.overall_risk > 0.7)
        avg_detection_gap = sum(score.detection_gap for score in risk_scores) / len(risk_scores)
        
        # Build detailed breakdown
        details = {}
        for score in risk_scores:
            details[score.mitre_id] = {
                "technique_name": score.technique_name,
                "likelihood": score.likelihood,
                "impact": score.impact,
                "detection_coverage": score.detection_coverage,
                "detection_gap": score.detection_gap,
                "overall_risk": score.overall_risk
            }
        
        snapshot = ReportSnapshot(
            total_techniques=len(risk_scores),
            avg_risk_score=avg_risk,
            high_risk_count=high_risk_count,
            detection_gap_avg=avg_detection_gap,
            details=details
        )
        db.add(snapshot)
        db.commit()
        db.refresh(snapshot)
        
        logger.info(f"Generated risk snapshot: {len(risk_scores)} techniques, avg risk {avg_risk:.3f}")
        return snapshot

    def bulk_calculate_all_techniques(self, db: Session, impact: float = 0.5) -> List[TechniqueRiskScore]:
        """Recalculate risk scores for all known techniques."""
        campaign_techniques = db.query(CampaignTechnique).distinct(
            CampaignTechnique.mitre_id
        ).all()
        
        results = []
        for camp_tech in campaign_techniques:
            score = self.calculate_risk_score(
                db,
                camp_tech.mitre_id,
                technique_name=camp_tech.name,
                impact=impact
            )
            results.append(score)
        
        logger.info(f"Calculated risk scores for {len(results)} techniques")
        return results

risk_engine = RiskScoringEngine()
