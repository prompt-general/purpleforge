from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class TechniqueBase(BaseModel):
    name: str = Field(..., description="Unique name of the technique")
    description: Optional[str] = None
    mitre_id: str = Field(..., description="MITRE ATT&CK ID, e.g., T1059.001")

class TechniqueCreate(BaseModel):
    name: str
    description: Optional[str] = None
    mitre_id: str

class TechniqueResponse(TechniqueBase):
    id: int

    class Config:
        from_attributes = True

class ExecutionBase(BaseModel):
    technique_id: int = Field(..., description="ID of the technique to execute")

class ExecutionCreate(ExecutionBase):
    pass

class ExecutionResponse(BaseModel):
    id: int
    technique_id: int
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    status: str
    cleanup_status: str
    logs: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

class ExecutionSummaryResponse(BaseModel):
    """Summary view for listings"""
    id: int
    technique_id: int
    status: str
    cleanup_status: str
    start_time: datetime
    
    class Config:
        from_attributes = True

class ExecutionStatusResponse(BaseModel):
    """Execution status for polling"""
    id: int
    status: str
    message: Optional[str] = None

    class Config:
        from_attributes = True

class DetectionRuleBase(BaseModel):
    technique_id: int
    name: str
    spl_query: str

class DetectionRuleCreate(DetectionRuleBase):
    pass

class DetectionRuleResponse(DetectionRuleBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class ValidationResultResponse(BaseModel):
    id: int
    execution_id: int
    is_detected: str
    matched_events_count: int
    validation_time: datetime
    logs: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

class ReportBase(BaseModel):
    name: str

class ReportCreate(ReportBase):
    pass

class ReportResponse(ReportBase):
    id: int
    created_at: datetime
    total_executions: int
    successful_detections: int
    failed_detections: int
    coverage_percentage: int
    details: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

# Spec 2: Milestone 1 - DAG Attack Chains
class AttackChainBase(BaseModel):
    name: str
    description: Optional[str] = None

class AttackChainCreate(AttackChainBase):
    pass

class AttackChainResponse(AttackChainBase):
    id: int

    class Config:
        from_attributes = True

class ChainNodeBase(BaseModel):
    chain_id: int
    technique_id: int
    name: str

class ChainNodeCreate(ChainNodeBase):
    pass

class ChainNodeResponse(ChainNodeBase):
    id: int

    class Config:
        from_attributes = True

class ChainEdgeBase(BaseModel):
    source_node_id: int
    target_node_id: int
    condition: str = "ALWAYS" # ALWAYS, ON_SUCCESS, ON_FAILURE
class ChainEdgeCreate(ChainEdgeBase):
    pass

class ChainEdgeResponse(ChainEdgeBase):
    id: int

    class Config:
        from_attributes = True

class ChainExecutionCreate(BaseModel):
    chain_id: int

class ChainExecutionResponse(BaseModel):
    id: int
    chain_id: int
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    status: str
    logs: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

# Spec 2: Milestone 4 - Collaboration schemas
class TenantBase(BaseModel):
    name: str

class TenantCreate(TenantBase):
    pass

class TenantResponse(TenantBase):
    id: int
    class Config:
        from_attributes = True

class UserBase(BaseModel):
    username: str
    role: str
    tenant_id: Optional[int] = None

class UserCreate(UserBase):
    pass

class UserResponse(UserBase):
    id: int
    class Config:
        from_attributes = True

class ExerciseBase(BaseModel):
    name: str
    description: Optional[str] = None

class ExerciseCreate(ExerciseBase):
    pass

class ExerciseResponse(ExerciseBase):
    id: int
    tenant_id: int
    status: str
    created_by_id: int
    start_time: Optional[datetime]
    end_time: Optional[datetime]

    class Config:
        from_attributes = True

class ExerciseUpdate(BaseModel):
    status: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

class ExerciseCommentBase(BaseModel):
    exercise_id: int
    comment: str

class ExerciseCommentCreate(ExerciseCommentBase):
    pass

class ExerciseCommentResponse(ExerciseCommentBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class AuditLogResponse(BaseModel):
    id: int
    user_id: int
    action: str
    target_type: Optional[str] = None
    target_id: Optional[int] = None
    timestamp: datetime

    class Config:
        from_attributes = True


# Spec 3: Threat Intel schemas (M1)
class CampaignTechniqueBase(BaseModel):
    mitre_id: str
    name: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None

class CampaignTechniqueCreate(CampaignTechniqueBase):
    pass

class CampaignTechniqueResponse(CampaignTechniqueBase):
    id: int
    campaign_id: int
    class Config:
        from_attributes = True

class ThreatCampaignBase(BaseModel):
    name: str
    description: Optional[str] = None
    external_id: Optional[str] = None

class ThreatCampaignCreate(ThreatCampaignBase):
    techniques: Optional[List[CampaignTechniqueCreate]] = None

class ThreatCampaignResponse(ThreatCampaignBase):
    id: int
    created_at: datetime
    techniques: Optional[List[CampaignTechniqueResponse]] = None

    class Config:
        from_attributes = True


# Spec 3: Asset and chain generation schemas (M2)
class AssetBase(BaseModel):
    name: str
    asset_type: str
    environment: Optional[str] = None
    tags: Optional[Dict[str, Any]] = None

class AssetCreate(AssetBase):
    pass

class AssetResponse(AssetBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class ChainGenerationRequest(BaseModel):
    campaign_id: int
    environment: Optional[str] = None
    asset_filter_tags: Optional[Dict[str, Any]] = None
    chain_name: Optional[str] = None

class GeneratedChainResponse(BaseModel):
    chain_id: int
    chain_name: str
    num_techniques: int
    num_nodes: int
    num_edges: int

    class Config:
        from_attributes = True


# Spec 3: Risk scoring schemas (M3)
class TechniqueRiskScoreResponse(BaseModel):
    mitre_id: str
    technique_name: Optional[str] = None
    likelihood: float
    impact: float
    detection_coverage: float
    detection_gap: float
    overall_risk: float
    calculated_at: datetime

    class Config:
        from_attributes = True

class ReportSnapshotResponse(BaseModel):
    id: int
    snapshot_date: datetime
    total_techniques: int
    avg_risk_score: float
    high_risk_count: int
    detection_gap_avg: float
    details: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True
