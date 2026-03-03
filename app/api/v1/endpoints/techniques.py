from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.models import Technique
from app.schemas.schemas import TechniqueCreate, TechniqueResponse

router = APIRouter()

@router.post("/", response_model=TechniqueResponse, status_code=201)
def create_technique(
    *,
    db: Session = Depends(get_db),
    technique_in: TechniqueCreate
) -> Any:
    """
    Create a new technique (admin functionality).
    """
    technique = db.query(Technique).filter(Technique.name == technique_in.name).first()
    if technique:
        raise HTTPException(status_code=400, detail="Technique name already exists")
    
    new_technique = Technique(
        name=technique_in.name,
        description=technique_in.description,
        mitre_id=technique_in.mitre_id
    )
    db.add(new_technique)
    db.commit()
    db.refresh(new_technique)
    return new_technique

@router.get("/", response_model=List[TechniqueResponse])
def list_techniques(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    List all available techniques.
    """
    techniques = db.query(Technique).offset(skip).limit(limit).all()
    return techniques

@router.get("/{id}", response_model=TechniqueResponse)
def get_technique(
    *,
    db: Session = Depends(get_db),
    id: int
) -> Any:
    """
    Get a specific technique by ID.
    """
    technique = db.query(Technique).filter(Technique.id == id).first()
    if not technique:
        raise HTTPException(status_code=404, detail="Technique not found")
    return technique
