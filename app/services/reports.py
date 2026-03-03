from sqlalchemy.orm import Session
from app.models.models import Report, Execution, ValidationResult, Technique
from datetime import datetime

def generate_coverage_report(db: Session, name: str) -> Report:
    """
    Generate a snapshot coverage report of all execution validation results.
    """
    # Fetch all validations
    validations = db.query(ValidationResult).all()
    
    total_executions = len(validations)
    successful_detections = sum(1 for v in validations if v.is_detected == "TRUE")
    failed_detections = sum(1 for v in validations if v.is_detected == "FALSE")
    
    coverage_percentage = 0
    if total_executions > 0:
        coverage_percentage = int((successful_detections / total_executions) * 100)
        
    details = {
        "summary": "Snapshot of current detection coverage",
        "validations_processed": total_executions,
        "true_positives": successful_detections,
        "false_negatives": failed_detections,
        "errors": sum(1 for v in validations if v.is_detected == "ERROR"),
        "pending": sum(1 for v in validations if v.is_detected == "PENDING")
    }
    
    report = Report(
        name=name,
        total_executions=total_executions,
        successful_detections=successful_detections,
        failed_detections=failed_detections,
        coverage_percentage=coverage_percentage,
        details=details
    )
    
    db.add(report)
    db.commit()
    db.refresh(report)
    
    return report
