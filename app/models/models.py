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
    
    # Relationship to executions and rules
    executions = relationship("Execution", back_populates="technique")
    detection_rules = relationship("DetectionRule", back_populates="technique")

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
    validation_results = relationship("ValidationResult", back_populates="execution")

class DetectionRule(Base):
    __tablename__ = "detection_rules"
    id = Column(Integer, primary_key=True, index=True)
    technique_id = Column(Integer, ForeignKey("techniques.id"), nullable=False)
    name = Column(String, index=True, nullable=False)
    spl_query = Column(String, nullable=False) # Splunk Processing Language query
    created_at = Column(DateTime, default=datetime.utcnow)
    
    technique = relationship("Technique", back_populates="detection_rules")

class ValidationResult(Base):
    __tablename__ = "validation_results"
    id = Column(Integer, primary_key=True, index=True)
    execution_id = Column(Integer, ForeignKey("executions.id"), nullable=False)
    is_detected = Column(String, default="PENDING") # PENDING, TRUE, FALSE, ERROR
    matched_events_count = Column(Integer, default=0)
    validation_time = Column(DateTime, default=datetime.utcnow)
    logs = Column(JSON, nullable=True) # Any Splunk logs or errors
    
    execution = relationship("Execution", back_populates="validation_results")

# Future models: Report

class Report(Base):
    __tablename__ = "reports"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    total_executions = Column(Integer, default=0)
    successful_detections = Column(Integer, default=0)
    failed_detections = Column(Integer, default=0)
    coverage_percentage = Column(Integer, default=0)
    details = Column(JSON, nullable=True) # Detailed list of techniques and their status
