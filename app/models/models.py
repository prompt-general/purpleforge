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
    cleanup_status = Column(String, default="PENDING") # PENDING, SUCCESS, FAILED
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

# Spec 2: Milestone 1 - DAG Attack Chains
class AttackChain(Base):
    __tablename__ = "attack_chains"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(String)
    nodes = relationship("ChainNode", back_populates="chain")
    executions = relationship("ChainExecution", back_populates="chain")

class ChainNode(Base):
    __tablename__ = "chain_nodes"
    id = Column(Integer, primary_key=True, index=True)
    chain_id = Column(Integer, ForeignKey("attack_chains.id"), nullable=False)
    technique_id = Column(Integer, ForeignKey("techniques.id"), nullable=False)
    name = Column(String, nullable=False)
    
    chain = relationship("AttackChain", back_populates="nodes")
    technique = relationship("Technique")
    
    outgoing_edges = relationship("ChainEdge", foreign_keys="[ChainEdge.source_node_id]", back_populates="source_node")
    incoming_edges = relationship("ChainEdge", foreign_keys="[ChainEdge.target_node_id]", back_populates="target_node")

class ChainEdge(Base):
    __tablename__ = "chain_edges"
    id = Column(Integer, primary_key=True, index=True)
    source_node_id = Column(Integer, ForeignKey("chain_nodes.id"), nullable=False)
    target_node_id = Column(Integer, ForeignKey("chain_nodes.id"), nullable=False)
    condition = Column(String, default="ALWAYS") # ALWAYS, ON_SUCCESS, ON_FAILURE
    
    source_node = relationship("ChainNode", foreign_keys=[source_node_id], back_populates="outgoing_edges")
    target_node = relationship("ChainNode", foreign_keys=[target_node_id], back_populates="incoming_edges")

class ChainExecution(Base):
    __tablename__ = "chain_executions"
    id = Column(Integer, primary_key=True, index=True)
    chain_id = Column(Integer, ForeignKey("attack_chains.id"), nullable=False)
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    status = Column(String, default="PENDING") # PENDING, RUNNING, COMPLETED, FAILED
    logs = Column(JSON, nullable=True) # Execution metadata/DAG execution path
    
    chain = relationship("AttackChain", back_populates="executions")

# Spec 2: Milestone 4 - Exercise collaboration
class Tenant(Base):
    __tablename__ = "tenants"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)

    users = relationship("User", back_populates="tenant")
    exercises = relationship("Exercise", back_populates="tenant")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    role = Column(String, nullable=False)  # Admin, Operator, Viewer
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True)

    tenant = relationship("Tenant", back_populates="users")
    comments = relationship("ExerciseComment", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")
    exercises_created = relationship("Exercise", back_populates="created_by")

class Exercise(Base):
    __tablename__ = "exercises"
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    status = Column(String, default="PENDING")
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)

    tenant = relationship("Tenant", back_populates="exercises")
    created_by = relationship("User", back_populates="exercises_created")
    comments = relationship("ExerciseComment", back_populates="exercise")

class ExerciseComment(Base):
    __tablename__ = "exercise_comments"
    id = Column(Integer, primary_key=True, index=True)
    exercise_id = Column(Integer, ForeignKey("exercises.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    comment = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    exercise = relationship("Exercise", back_populates="comments")
    user = relationship("User", back_populates="comments")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String, nullable=False)
    target_type = Column(String, nullable=True)
    target_id = Column(Integer, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="audit_logs")


# Spec 3: Threat Intel (M1 - Campaign ingestion)
class ThreatCampaign(Base):
    __tablename__ = "threat_campaigns"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(String, nullable=True)
    external_id = Column(String, nullable=True)  # e.g., STIX campaign id
    created_at = Column(DateTime, default=datetime.utcnow)

    techniques = relationship("CampaignTechnique", back_populates="campaign")


class CampaignTechnique(Base):
    __tablename__ = "campaign_techniques"
    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("threat_campaigns.id"), nullable=False)
    mitre_id = Column(String, nullable=False, index=True)
    name = Column(String, nullable=True)
    meta = Column(JSON, nullable=True)

    campaign = relationship("ThreatCampaign", back_populates="techniques")


class Asset(Base):
    __tablename__ = "assets"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    asset_type = Column(String, nullable=False)  # e.g., "ec2-instance", "s3-bucket", "windows-host"
    environment = Column(String, nullable=True)  # e.g., "prod", "staging", "dev"
    tags = Column(JSON, nullable=True)  # arbitrary tags for filtering
    created_at = Column(DateTime, default=datetime.utcnow)

    technique_compatibility = relationship("TechniqueAssetMap", back_populates="asset")


class TechniqueAssetMap(Base):
    __tablename__ = "technique_asset_map"
    id = Column(Integer, primary_key=True, index=True)
    mitre_id = Column(String, nullable=False, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    compatible = Column(Boolean, default=True)  # whether technique can run on this asset

    asset = relationship("Asset", back_populates="technique_compatibility")


class TechniqueRiskScore(Base):
    __tablename__ = "technique_risk_scores"
    id = Column(Integer, primary_key=True, index=True)
    mitre_id = Column(String, nullable=False, unique=True)
    technique_name = Column(String, nullable=True)
    likelihood = Column(Float, default=0.0)  # 0.0 - 1.0: frequency in campaigns
    impact = Column(Float, default=0.5)  # 0.0 - 1.0: criticality impact
    detection_coverage = Column(Float, default=0.0)  # 0.0 - 1.0: % detections vs executions
    detection_gap = Column(Float, default=1.0)  # 1.0 - detection_coverage
    overall_risk = Column(Float, default=0.0)  # likelihood × impact × detection_gap
    calculated_at = Column(DateTime, default=datetime.utcnow)


class ReportSnapshot(Base):
    __tablename__ = "report_snapshots"
    id = Column(Integer, primary_key=True, index=True)
    snapshot_date = Column(DateTime, default=datetime.utcnow)
    total_techniques = Column(Integer, default=0)
    avg_risk_score = Column(Float, default=0.0)
    high_risk_count = Column(Integer, default=0)  # techniques with risk > 0.7
    detection_gap_avg = Column(Float, default=0.0)
    details = Column(JSON, nullable=True)  # detailed per-technique scores

    # relationship to track which techniques were included
    created_at = Column(DateTime, default=datetime.utcnow)


class Integration(Base):
    __tablename__ = "integrations"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    integration_type = Column(String, nullable=False)  # "webhook", "jira", "servicenow", "splunk", "soar"
    config = Column(JSON, nullable=False)  # url, credentials, etc.
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    events = relationship("IntegrationEvent", back_populates="integration")
    tickets = relationship("Ticket", back_populates="integration")


class IntegrationEvent(Base):
    __tablename__ = "integration_events"
    id = Column(Integer, primary_key=True, index=True)
    integration_id = Column(Integer, ForeignKey("integrations.id"), nullable=False)
    event_type = Column(String, nullable=False)  # "high_risk_detected", "detection_gap", "snapshot_generated"
    payload = Column(JSON, nullable=True)
    sent_at = Column(DateTime, default=datetime.utcnow)
    success = Column(Boolean, default=False)
    error_message = Column(String, nullable=True)
    
    integration = relationship("Integration", back_populates="events")


class Ticket(Base):
    __tablename__ = "tickets"
    id = Column(Integer, primary_key=True, index=True)
    integration_id = Column(Integer, ForeignKey("integrations.id"), nullable=False)
    external_ticket_id = Column(String, nullable=True)  # ticket ID in external system (e.g., JIRA-123)
    mitre_id = Column(String, nullable=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    ticket_type = Column(String, default="DETECTION_GAP")  # DETECTION_GAP, HIGH_RISK, etc.
    created_at = Column(DateTime, default=datetime.utcnow)
    closed_at = Column(DateTime, nullable=True)
    
    integration = relationship("Integration", back_populates="tickets")
