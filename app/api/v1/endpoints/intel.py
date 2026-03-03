from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.models import ThreatCampaign, Asset, TechniqueRiskScore, ReportSnapshot
from app.services.intel import intel_service
from app.services.chain_generation import chain_generation_service
from app.services.risk_engine import risk_engine
from app.schemas.schemas import (
    ThreatCampaignCreate, ThreatCampaignResponse,
    AssetCreate, AssetResponse,
    ChainGenerationRequest, GeneratedChainResponse,
    TechniqueRiskScoreResponse, ReportSnapshotResponse
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

# --- Risk scoring endpoints (M3) ---
@router.post("/risk/calculate-all", response_model=List[TechniqueRiskScoreResponse], status_code=201)
def calculate_all_risks(
    impact: float = 0.5,
    db: Session = Depends(get_db)
) -> Any:
    """Calculate or update risk scores for all known techniques."""
    scores = risk_engine.bulk_calculate_all_techniques(db, impact=impact)
    return scores

@router.get("/risk/scores", response_model=List[TechniqueRiskScoreResponse])
def list_risk_scores(
    min_risk: float = None,
    db: Session = Depends(get_db)
) -> Any:
    """List all technique risk scores, optionally filtered by minimum risk."""
    query = db.query(TechniqueRiskScore)
    if min_risk is not None:
        query = query.filter(TechniqueRiskScore.overall_risk >= min_risk)
    return query.order_by(TechniqueRiskScore.overall_risk.desc()).all()

@router.get("/risk/scores/{mitre_id}", response_model=TechniqueRiskScoreResponse)
def get_risk_score(
    mitre_id: str,
    db: Session = Depends(get_db)
) -> Any:
    """Get risk score for a specific technique."""
    score = db.query(TechniqueRiskScore).filter(
        TechniqueRiskScore.mitre_id == mitre_id
    ).first()
    if not score:
        raise HTTPException(status_code=404, detail="Risk score not found")
    return score

@router.post("/risk/snapshot", response_model=ReportSnapshotResponse, status_code=201)
def generate_risk_snapshot(db: Session = Depends(get_db)) -> Any:
    """Generate a risk report snapshot at this moment in time."""
    snapshot = risk_engine.generate_risk_snapshot(db)
    return snapshot

@router.get("/risk/snapshots", response_model=List[ReportSnapshotResponse])
def list_snapshots(db: Session = Depends(get_db)) -> Any:
    """List historical risk snapshots."""
    snapshots = db.query(ReportSnapshot).order_by(
        ReportSnapshot.snapshot_date.desc()
    ).all()
    return snapshots

@router.get("/risk/snapshots/{snapshot_id}", response_model=ReportSnapshotResponse)
def get_snapshot(snapshot_id: int, db: Session = Depends(get_db)) -> Any:
    """Get a specific risk snapshot by ID."""
    snapshot = db.query(ReportSnapshot).filter(ReportSnapshot.id == snapshot_id).first()
    if not snapshot:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    return snapshot
