import logging
from datetime import datetime
from app.core.celery_app import celery_app
from app.services.stratus import stratus_service
from app.services.splunk import splunk_service
from app.services.chains import dag_engine
from app.db.session import SessionLocal
from app.models.models import Execution, DetectionRule, ValidationResult, ChainExecution, ChainNode
import time

logger = logging.getLogger(__name__)

@celery_app.task(name="run_technique_task", bind=True)
def run_technique_task(self, execution_id: int, mitre_technique_id: str):
    """
    Async task to execute a technique via Stratus and update the database.
    """
    logger.info(f"Starting execution ID: {execution_id} for technique {mitre_technique_id}")
    
    db = SessionLocal()
    execution = db.query(Execution).filter(Execution.id == execution_id).first()
    
    if not execution:
        logger.error(f"Execution {execution_id} not found")
        db.close()
        return {"status": "ERROR", "message": "Execution ID not found"}
    
    try:
        # 1. Update status to RUNNING
        execution.status = "RUNNING"
        db.commit()
        
        # 2. Execute (Warmup + Detonate + Cleanup)
        # For simplicity in M1, we just detonate directly
        # In M2, we'll wait for SIEM ingestion before status update
        stratus_service.warmup(mitre_technique_id)
        results = stratus_service.detonate(mitre_technique_id)
        stratus_service.cleanup(mitre_technique_id)
        
        # 3. Update DB with Results
        execution.status = results.get("status", "COMPLETED")
        execution.end_time = datetime.utcnow()
        execution.logs = results
        db.commit()
        
        # 4. Milestone 2: Splunk Validation
        # Get mapping rule
        rule = db.query(DetectionRule).filter(DetectionRule.technique_id == execution.technique_id).first()
        
        if rule:
            logger.info(f"Rule found for technique {mitre_technique_id}. Waiting for logs to ingest...")
            # Simple sleep for M2 (in prod, use task chaining with delays)
            time.sleep(10)
            
            search_results = splunk_service.search(
                spl_query=rule.spl_query,
                start_time=execution.start_time,
                end_time=execution.end_time or datetime.utcnow()
            )
            
            is_detected = "TRUE" if search_results.get("count", 0) > 0 else "FALSE"
            if search_results.get("status") == "ERROR":
                is_detected = "ERROR"
            
            validation = ValidationResult(
                execution_id=execution.id,
                is_detected=is_detected,
                matched_events_count=search_results.get("count", 0),
                logs=search_results
            )
            db.add(validation)
            db.commit()
            logger.info(f"Validation complete for {execution_id}: {is_detected}")
        else:
            logger.info(f"No detection rule mapped for technique {mitre_technique_id}.")
        
        logger.info(f"Successfully completed execution {execution_id}")
        return results

    except Exception as e:
        logger.error(f"Failed to execute {execution_id}: {str(e)}")
        execution.status = "FAILED"
        execution.end_time = datetime.utcnow()
        execution.logs = {"error": str(e)}
        db.commit()
        return {"status": "FAILED", "error": str(e)}
    finally:
        db.close()

@celery_app.task(name="run_chain_task", bind=True)
def run_chain_task(self, chain_execution_id: int):
    """
    Async task to execute an Attack Chain topologically.
    """
    logger.info(f"Starting Chain Execution ID: {chain_execution_id}")
    
    db = SessionLocal()
    execution = db.query(ChainExecution).filter(ChainExecution.id == chain_execution_id).first()
    
    if not execution:
        logger.error(f"Chain Execution {chain_execution_id} not found")
        db.close()
        return {"status": "ERROR"}
        
    try:
        execution.status = "RUNNING"
        db.commit()
        
        # Load chain nodes and edges
        chain = execution.chain
        nodes = chain.nodes
        
        # Extract edges (since edges point to node IDs, we can gather all edges where source_node is in nodes)
        # For simplicity, we can load edges directly mapped to nodes
        edges = []
        for n in nodes:
            edges.extend(n.outgoing_edges)
            
        # Get topological sorted order
        execution_order = dag_engine.get_execution_order(nodes, edges)
        
        chain_logs = {"execution_path": []}
        
        for node in execution_order:
            logger.info(f"Executing Chain Node: {node.name} (Technique: {node.technique.mitre_id})")
            
            # Create a sub-execution for the technique execution (reusing the individual execution table)
            sub_exec = Execution(
                technique_id=node.technique_id,
                status="PENDING"
            )
            db.add(sub_exec)
            db.commit()
            db.refresh(sub_exec)
            
            # We call the individual task code directly synchronously here for the chain MVP
            # (In reality, we could `.delay()` and use Celery chords/chains, but a sync loop is easier to track for MVP)
            # Actually, instead of replicating logic, we could just extract the logic of `run_technique_task` or call it as a normal function.
            # To keep it simple, we'll re-implement the core loop.
            
            stratus_service.warmup(node.technique.mitre_id)
            results = stratus_service.detonate(node.technique.mitre_id)
            stratus_service.cleanup(node.technique.mitre_id)
            
            sub_exec.status = results.get("status", "COMPLETED")
            sub_exec.end_time = datetime.utcnow()
            sub_exec.logs = results
            db.commit()
            
            # M2 Integration inside Chain
            rule = db.query(DetectionRule).filter(DetectionRule.technique_id == node.technique_id).first()
            is_detected = "PENDING"
            if rule:
                time.sleep(10)
                search_results = splunk_service.search(
                    spl_query=rule.spl_query,
                    start_time=sub_exec.start_time,
                    end_time=sub_exec.end_time or datetime.utcnow()
                )
                is_detected = "TRUE" if search_results.get("count", 0) > 0 else "FALSE"
                if search_results.get("status") == "ERROR": is_detected = "ERROR"
                
                validation = ValidationResult(
                    execution_id=sub_exec.id,
                    is_detected=is_detected,
                    matched_events_count=search_results.get("count", 0),
                    logs=search_results
                )
                db.add(validation)
                db.commit()
            
            chain_logs["execution_path"].append({
                "node_id": node.id,
                "technique_id": node.technique_id,
                "mitre_id": node.technique.mitre_id,
                "execution_status": sub_exec.status,
                "detection_status": is_detected
            })
            
            if sub_exec.status == "FAILED":
                # For M1, we fail the whole chain if one step fails. M2 will support conditionals.
                execution.status = "FAILED"
                execution.end_time = datetime.utcnow()
                execution.logs = chain_logs
                db.commit()
                return chain_logs

        execution.status = "COMPLETED"
        execution.end_time = datetime.utcnow()
        execution.logs = chain_logs
        db.commit()
        return chain_logs

    except Exception as e:
        logger.error(f"Chain execution failed: {str(e)}")
        execution.status = "FAILED"
        execution.logs = {"error": str(e)}
        execution.end_time = datetime.utcnow()
        db.commit()
        return {"status": "FAILED"}
    finally:
        db.close()
