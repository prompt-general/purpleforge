import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models.models import (
    ThreatCampaign, CampaignTechnique, Technique,
    AttackChain, ChainNode, ChainEdge, Asset, TechniqueAssetMap
)

logger = logging.getLogger(__name__)

class ChainGenerationService:
    """Service to auto-generate attack chains from threat campaigns.
    
    For M2:
    1. Select campaign
    2. Filter techniques by environment + asset compatibility
    3. Build a simple linear DAG (technique1 -> technique2 -> ... -> techniqueN)
    4. Store the chain with nodes and edges
    """

    def generate_chain_from_campaign(
        self,
        db: Session,
        campaign_id: int,
        environment: Optional[str] = None,
        asset_filter_tags: Optional[Dict[str, Any]] = None,
        chain_name: Optional[str] = None
    ) -> AttackChain:
        """Generate an attack chain from a campaign, filtered by environment and assets."""
        
        # Load campaign
        campaign = db.query(ThreatCampaign).filter(ThreatCampaign.id == campaign_id).first()
        if not campaign:
            raise ValueError("Campaign not found")
        
        # Get campaign techniques
        camp_techniques = db.query(CampaignTechnique).filter(
            CampaignTechnique.campaign_id == campaign_id
        ).all()
        
        if not camp_techniques:
            raise ValueError("Campaign has no techniques")
        
        # Filter techniques by environment and asset compatibility
        compatible_techniques = []
        for camp_tech in camp_techniques:
            # Check if environment and asset compatibility match
            if self._is_technique_compatible(db, camp_tech.mitre_id, environment, asset_filter_tags):
                compatible_techniques.append(camp_tech)
        
        if not compatible_techniques:
            raise ValueError("No compatible techniques found for the specified environment/assets")
        
        # Get or create the base Technique objects for each campaign technique
        technique_objs = []
        for camp_tech in compatible_techniques:
            tech = db.query(Technique).filter(Technique.mitre_id == camp_tech.mitre_id).first()
            if not tech:
                # Create a base technique if it doesn't exist
                tech = Technique(
                    name=camp_tech.name or f"Technique {camp_tech.mitre_id}",
                    mitre_id=camp_tech.mitre_id,
                    description=f"Technique from campaign {campaign.name}"
                )
                db.add(tech)
                db.commit()
                db.refresh(tech)
            technique_objs.append((camp_tech, tech))
        
        # Create the attack chain
        chain_name = chain_name or f"{campaign.name} Attack Chain"
        chain = AttackChain(
            name=chain_name,
            description=f"Auto-generated chain from campaign {campaign.name} ({len(technique_objs)} techniques)"
        )
        db.add(chain)
        db.commit()
        db.refresh(chain)
        
        # Create chain nodes (one per technique)
        nodes = []
        for idx, (camp_tech, tech) in enumerate(technique_objs):
            node = ChainNode(
                chain_id=chain.id,
                technique_id=tech.id,
                name=tech.name
            )
            db.add(node)
            db.commit()
            db.refresh(node)
            nodes.append(node)
        
        # Create chain edges (linear: node[i] -> node[i+1])
        for i in range(len(nodes) - 1):
            edge = ChainEdge(
                source_node_id=nodes[i].id,
                target_node_id=nodes[i + 1].id,
                condition="ALWAYS"
            )
            db.add(edge)
        
        db.commit()
        return chain

    def _is_technique_compatible(
        self,
        db: Session,
        mitre_id: str,
        environment: Optional[str] = None,
        asset_filter_tags: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Check if a technique is compatible with the specified environment and assets."""
        
        # If no environment specified, technique is compatible with any
        if not environment and not asset_filter_tags:
            return True
        
        # Query assets matching environment and tags
        assets_query = db.query(Asset)
        if environment:
            assets_query = assets_query.filter(Asset.environment == environment)
        
        assets = assets_query.all()
        if not assets:
            return False
        
        # Filter further if tag filter provided
        matching_assets = []
        for asset in assets:
            if asset_filter_tags is None:
                matching_assets.append(asset)
            elif asset.tags and all(
                asset.tags.get(k) == v for k, v in asset_filter_tags.items()
            ):
                matching_assets.append(asset)
        
        if not matching_assets:
            return False
        
        # Check if technique is compatible with at least one asset
        for asset in matching_assets:
            compatibility = db.query(TechniqueAssetMap).filter(
                TechniqueAssetMap.mitre_id == mitre_id,
                TechniqueAssetMap.asset_id == asset.id,
                TechniqueAssetMap.compatible == True
            ).first()
            if compatibility:
                return True
        
        return False

chain_generation_service = ChainGenerationService()
