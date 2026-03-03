from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.models import DetectionRule, Technique
from app.schemas.schemas import DetectionRuleCreate, DetectionRuleResponse

router = APIRouter()

@router.post("/", response_model=DetectionRuleResponse, status_code=201)
def create_detection_rule(
    *,
    db: Session = Depends(get_db),
    rule_in: DetectionRuleCreate
) -> Any:
    """
    Map a technique to a detection rule (SIEM SPL Query).
    """
    technique = db.query(Technique).filter(Technique.id == rule_in.technique_id).first()
    if not technique:
        raise HTTPException(status_code=404, detail="Technique not found")
        
    rule = DetectionRule(
        technique_id=rule_in.technique_id,
        name=rule_in.name,
        spl_query=rule_in.spl_query
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule

@router.get("/", response_model=List[DetectionRuleResponse])
def list_detection_rules(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    List all mapped detection rules.
    """
    rules = db.query(DetectionRule).offset(skip).limit(limit).all()
    return rules
