from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship, DeclarativeBase

class Base(DeclarativeBase):
    pass

class Technique(Base):
    __tablename__ = "techniques"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String)
    mitre_id = Column(String, index=True)
    
    # Relationship to executions
    executions = relationship("Execution", back_populates="technique")

class Execution(Base):
    __tablename__ = "executions"
    id = Column(Integer, primary_key=True, index=True)
    technique_id = Column(Integer, ForeignKey("techniques.id"), nullable=False)
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    status = Column(String, default="PENDING") # PENDING, RUNNING, COMPLETED, FAILED
    logs = Column(JSON, nullable=True) # Execution metadata and output
    
    # Relationship to technique
    technique = relationship("Technique", back_populates="executions")
    
    # Placeholder for Milestone 2: validation results
    # validation_results = relationship("ValidationResult", back_populates="execution")

# Future models: DetectionRule, ValidationResult, Report
