from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.models import ThreatCampaign, Asset
from app.services.intel import intel_service
from app.services.chain_generation import chain_generation_service
from app.schemas.schemas import (
    ThreatCampaignCreate, ThreatCampaignResponse,
    AssetCreate, AssetResponse,
    ChainGenerationRequest, GeneratedChainResponse
)

router = APIRouter()

# --- Campaign endpoints ---
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

# --- Asset endpoints (M2) ---
@router.post("/assets", response_model=AssetResponse, status_code=201)
def register_asset(*, db: Session = Depends(get_db), asset_in: AssetCreate) -> Any:
    """Register an environment asset (e.g., cloud resource, host, container)."""
    asset = Asset(
        name=asset_in.name,
        asset_type=asset_in.asset_type,
        environment=asset_in.environment,
        tags=asset_in.tags
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset

@router.get("/assets", response_model=List[AssetResponse])
def list_assets(
    environment: str = None,
    db: Session = Depends(get_db)
) -> Any:
    """List all registered assets, optionally filtered by environment."""
    query = db.query(Asset)
    if environment:
        query = query.filter(Asset.environment == environment)
    return query.all()

@router.get("/assets/{asset_id}", response_model=AssetResponse)
def get_asset(asset_id: int, db: Session = Depends(get_db)) -> Any:
    """Get a specific asset by ID."""
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset

# --- Chain generation endpoint (M2) ---
@router.post("/campaigns/{campaign_id}/generate-chain", response_model=GeneratedChainResponse, status_code=201)
def generate_chain_from_campaign(
    campaign_id: int,
    *,
    db: Session = Depends(get_db),
    request: ChainGenerationRequest
) -> Any:
    """Auto-generate an attack chain from a campaign, filtered by environment and assets."""
    try:
        chain = chain_generation_service.generate_chain_from_campaign(
            db,
            campaign_id,
            environment=request.environment,
            asset_filter_tags=request.asset_filter_tags,
            chain_name=request.chain_name
        )
        return GeneratedChainResponse(
            chain_id=chain.id,
            chain_name=chain.name,
            num_techniques=len([t for t in chain.nodes]),
            num_nodes=len(chain.nodes),
            num_edges=sum(len(n.outgoing_edges) for n in chain.nodes)
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
