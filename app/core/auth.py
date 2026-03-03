from fastapi import Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.models.models import User


def get_current_user(
    user_id: int = Header(..., alias="X-User-Id"),
    db: Session = Depends(get_db)
) -> User:
    """Retrieve the currently acting user from a header. """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or missing user")
    return user


def require_role(*roles: List[str]):
    """Dependency generator that enforces the current user has one of the specified roles."""
    def role_checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="Operation not permitted for your role")
        return user
    return Depends(role_checker)
