from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.models import ThreatCampaign
from app.services.intel import intel_service
from app.schemas.schemas import ThreatCampaignCreate, ThreatCampaignResponse

router = APIRouter()

@router.post("/campaigns", response_model=ThreatCampaignResponse, status_code=201)
def ingest_campaign(*, db: Session = Depends(get_db), payload: ThreatCampaignCreate) -> Any:
    """Ingest a threat campaign + its techniques."""
    try:
        campaign = intel_service.ingest_campaign(db, payload.dict())
        return campaign
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/campaigns", response_model=List[ThreatCampaignResponse])
def list_campaigns(db: Session = Depends(get_db)) -> Any:
    """List all ingested threat campaigns."""
    campaigns = db.query(ThreatCampaign).all()
    return campaigns

@router.get("/campaigns/{campaign_id}", response_model=ThreatCampaignResponse)
def get_campaign(campaign_id: int, db: Session = Depends(get_db)) -> Any:
    """Get a specific campaign by ID."""
    c = db.query(ThreatCampaign).filter(ThreatCampaign.id == campaign_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return c
