import logging
from datetime import datetime
from app.core.celery_app import celery_app
from app.services.stratus import stratus_service
from app.db.session import SessionLocal
from app.models.models import Execution

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
