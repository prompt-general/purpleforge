from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.models import AttackChain, ChainNode, ChainEdge, Technique, ChainExecution
from app.schemas.schemas import (
    AttackChainCreate, AttackChainResponse,
    ChainNodeCreate, ChainNodeResponse,
    ChainEdgeCreate, ChainEdgeResponse,
    ChainExecutionCreate, ChainExecutionResponse
)
from app.tasks.tasks import run_chain_task

router = APIRouter()

@router.post("/", response_model=AttackChainResponse, status_code=201)
def create_chain(
    *, db: Session = Depends(get_db), chain_in: AttackChainCreate
) -> Any:
    """Create a new Attack Chain (DAG container)."""
    chain = AttackChain(name=chain_in.name, description=chain_in.description)
    db.add(chain)
    db.commit()
    db.refresh(chain)
    return chain

@router.post("/nodes", response_model=ChainNodeResponse, status_code=201)
def add_chain_node(
    *, db: Session = Depends(get_db), node_in: ChainNodeCreate
) -> Any:
    """Add a node (technique step) to a chain."""
    chain = db.query(AttackChain).filter(AttackChain.id == node_in.chain_id).first()
    if not chain: raise HTTPException(status_code=404, detail="Chain not found")
    
    technique = db.query(Technique).filter(Technique.id == node_in.technique_id).first()
    if not technique: raise HTTPException(status_code=404, detail="Technique not found")
        
    node = ChainNode(chain_id=node_in.chain_id, technique_id=node_in.technique_id, name=node_in.name)
    db.add(node)
    db.commit()
    db.refresh(node)
    return node

@router.post("/edges", response_model=ChainEdgeResponse, status_code=201)
def add_chain_edge(
    *, db: Session = Depends(get_db), edge_in: ChainEdgeCreate
) -> Any:
    """Add a directional edge between two nodes in a chain."""
    source = db.query(ChainNode).filter(ChainNode.id == edge_in.source_node_id).first()
    target = db.query(ChainNode).filter(ChainNode.id == edge_in.target_node_id).first()
    if not source or not target:
        raise HTTPException(status_code=404, detail="Source or Target node not found")
        
    if source.chain_id != target.chain_id:
        raise HTTPException(status_code=400, detail="Nodes must belong to same chain")
        
    edge = ChainEdge(source_node_id=edge_in.source_node_id, target_node_id=edge_in.target_node_id)
    db.add(edge)
    db.commit()
    db.refresh(edge)
    return edge

@router.post("/execute", response_model=ChainExecutionResponse, status_code=201)
def execute_chain(
    *, db: Session = Depends(get_db), exec_in: ChainExecutionCreate
) -> Any:
    """Trigger the topological execution of an entire chain."""
    chain = db.query(AttackChain).filter(AttackChain.id == exec_in.chain_id).first()
    if not chain: raise HTTPException(status_code=404, detail="Chain not found")
    
    execution = ChainExecution(chain_id=chain.id)
    db.add(execution)
    db.commit()
    db.refresh(execution)
    
    # Trigger celery task
    run_chain_task.delay(execution.id)
    return execution

@router.get("/{id}/executions", response_model=List[ChainExecutionResponse])
def get_chain_executions(
    id: int, db: Session = Depends(get_db)
) -> Any:
    executions = db.query(ChainExecution).filter(ChainExecution.chain_id == id).all()
    return executions
