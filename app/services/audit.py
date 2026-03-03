from sqlalchemy.orm import Session
from app.models.models import AuditLog


def log_action(db: Session, user_id: int, action: str, target_type: str = None, target_id: int = None):
    """Persist a simple audit log entry."""
    entry = AuditLog(
        user_id=user_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry
