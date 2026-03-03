import json
import logging
from typing import Dict, Any, List
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.models import ThreatCampaign, CampaignTechnique

logger = logging.getLogger(__name__)

class IntelIngestor:
    """Simple threat intel ingestion service.

    For M1 we accept a STIX-like JSON payload (or simple campaign + techniques list)
    and persist campaign + technique mappings.
    """

    def ingest_campaign(self, db: Session, payload: Dict[str, Any]) -> ThreatCampaign:
        # payload expected keys: name, description, external_id, techniques: [{mitre_id,name,meta}]
        name = payload.get("name")
        if not name:
            raise ValueError("campaign name required")

        # upsert campaign by name
        existing = db.query(ThreatCampaign).filter(ThreatCampaign.name == name).first()
        if existing:
            campaign = existing
            campaign.description = payload.get("description")
            campaign.external_id = payload.get("external_id")
        else:
            campaign = ThreatCampaign(
                name=name,
                description=payload.get("description"),
                external_id=payload.get("external_id")
            )
            db.add(campaign)
            db.commit()
            db.refresh(campaign)

        # ingest techniques
        techniques = payload.get("techniques", [])
        for t in techniques:
            mitre = t.get("mitre_id")
            if not mitre:
                continue
            exists = db.query(CampaignTechnique).filter(
                CampaignTechnique.campaign_id == campaign.id,
                CampaignTechnique.mitre_id == mitre
            ).first()
            if exists:
                exists.name = t.get("name")
                exists.meta = t.get("meta")
            else:
                ct = CampaignTechnique(
                    campaign_id=campaign.id,
                    mitre_id=mitre,
                    name=t.get("name"),
                    meta=t.get("meta")
                )
                db.add(ct)
        db.commit()
        db.refresh(campaign)
        return campaign

intel_service = IntelIngestor()
