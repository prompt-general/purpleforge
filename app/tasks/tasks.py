import logging
from datetime import datetime
from app.core.celery_app import celery_app
from app.services.stratus import stratus_service
from app.services.splunk import splunk_service
from app.db.session import SessionLocal
from app.models.models import Execution, DetectionRule, ValidationResult
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
