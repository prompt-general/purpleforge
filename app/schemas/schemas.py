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
    logs: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

class ExecutionSummaryResponse(BaseModel):
    """Summary view for listings"""
    id: int
    technique_id: int
    status: str
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
