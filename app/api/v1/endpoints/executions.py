from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.models import Execution, Technique
from app.schemas.schemas import ExecutionCreate, ExecutionResponse, ExecutionSummaryResponse, ExecutionStatusResponse
from app.tasks.tasks import run_technique_task

router = APIRouter()

@router.post("/", response_model=ExecutionResponse, status_code=201)
def create_execution(
    *,
    db: Session = Depends(get_db),
    execution_in: ExecutionCreate
) -> Any:
    """
    Create a new attack execution.
    Triggers an async task via Celery to run the simulation.
    """
    # 1. Validate technique exists
    technique = db.query(Technique).filter(Technique.id == execution_in.technique_id).first()
    if not technique:
        raise HTTPException(status_code=404, detail="Technique not found")
    
    # 2. Persist execution record in PENDING state
    execution = Execution(
        technique_id=execution_in.technique_id,
        status="PENDING"
    )
    db.add(execution)
    db.commit()
    db.refresh(execution)
    
    # 3. Trigger async task
    run_technique_task.delay(execution.id, technique.mitre_id)
    
    return execution

@router.get("/", response_model=List[ExecutionSummaryResponse])
def list_executions(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve all executions.
    """
    executions = db.query(Execution).offset(skip).limit(limit).all()
    return executions

@router.get("/{id}", response_model=ExecutionResponse)
def get_execution(
    *,
    db: Session = Depends(get_db),
    id: int
) -> Any:
    """
    Get details of a specific execution.
    """
    execution = db.query(Execution).filter(Execution.id == id).first()
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    return execution

@router.get("/{id}/status", response_model=ExecutionStatusResponse)
def get_execution_status(
    *,
    db: Session = Depends(get_db),
    id: int
) -> Any:
    """
    Get the status of a specific execution (for polling).
    """
    execution = db.query(Execution).filter(Execution.id == id).first()
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    return execution
