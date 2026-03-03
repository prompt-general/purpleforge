from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from datetime import datetime

from app.db.session import get_db
from app.models.models import (
    Tenant, User, Exercise, ExerciseComment, AuditLog
)
from app.schemas.schemas import (
    TenantCreate, TenantResponse,
    UserCreate, UserResponse,
    ExerciseCreate, ExerciseResponse, ExerciseUpdate,
    ExerciseCommentCreate, ExerciseCommentResponse,
    AuditLogResponse
)
from app.core.auth import get_current_user, require_role
from app.services.audit import log_action

router = APIRouter()

# --- tenant endpoints (admin only) ---
@router.post("/tenants", response_model=TenantResponse, status_code=201,
             dependencies=[Depends(require_role("Admin"))])
def create_tenant(*, db: Session = Depends(get_db), tenant_in: TenantCreate) -> Any:
    tenant = Tenant(name=tenant_in.name)
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant

@router.get("/tenants", response_model=List[TenantResponse],
            dependencies=[Depends(require_role("Admin"))])
def list_tenants(db: Session = Depends(get_db)) -> Any:
    return db.query(Tenant).all()

# --- user endpoints (admin only) ---
@router.post("/users", response_model=UserResponse, status_code=201)
def create_user(
    *,
    db: Session = Depends(get_db),
    user_in: UserCreate,
    x_user_id: int | None = Header(None, alias="X-User-Id")
) -> Any:
    # allow bootstrap of first user without authentication
    total_users = db.query(User).count()
    if total_users > 0:
        # existing install, enforce admin privileges
        if x_user_id is None:
            raise HTTPException(status_code=401, detail="Missing X-User-Id header")
        current = db.query(User).filter(User.id == x_user_id).first()
        if not current or current.role != "Admin":
            raise HTTPException(status_code=403, detail="Admin role required to create users")
    else:
        # first signup: user must be admin
        if user_in.role != "Admin":
            raise HTTPException(status_code=400, detail="first user must have Admin role")

    # ensure tenant exists if provided
    if user_in.tenant_id:
        tenant = db.query(Tenant).filter(Tenant.id == user_in.tenant_id).first()
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
    user = User(username=user_in.username, role=user_in.role, tenant_id=user_in.tenant_id)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.get("/users", response_model=List[UserResponse],
            dependencies=[Depends(require_role("Admin"))])
def list_users(db: Session = Depends(get_db)) -> Any:
    return db.query(User).all()

# --- exercise endpoints ---
@router.post("/exercises", response_model=ExerciseResponse, status_code=201,
             dependencies=[Depends(require_role("Admin", "Operator"))])
def create_exercise(
    *,
    db: Session = Depends(get_db),
    exercise_in: ExerciseCreate,
    current_user: User = Depends(get_current_user)
) -> Any:
    # assign tenant by creator (admin may override by passing different tenant later if needed)
    tenant_id = current_user.tenant_id
    exercise = Exercise(
        tenant_id=tenant_id,
        name=exercise_in.name,
        description=exercise_in.description,
        status="PENDING",
        created_by_id=current_user.id,
    )
    db.add(exercise)
    db.commit()
    db.refresh(exercise)
    log_action(db, current_user.id, "create_exercise", "exercise", exercise.id)
    return exercise

@router.get("/exercises", response_model=List[ExerciseResponse])
def list_exercises(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    query = db.query(Exercise)
    if current_user.role != "Admin":
        query = query.filter(Exercise.tenant_id == current_user.tenant_id)
    return query.all()

@router.get("/exercises/{exercise_id}", response_model=ExerciseResponse)
def get_exercise(
    exercise_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    exercise = db.query(Exercise).filter(Exercise.id == exercise_id).first()
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")
    if current_user.role != "Admin" and exercise.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Not permitted to view this exercise")
    return exercise

@router.patch("/exercises/{exercise_id}", response_model=ExerciseResponse,
              dependencies=[Depends(require_role("Admin", "Operator"))])
def update_exercise(
    exercise_id: int,
    update_in: ExerciseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    exercise = db.query(Exercise).filter(Exercise.id == exercise_id).first()
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")
    if current_user.role != "Admin" and exercise.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Not permitted to modify this exercise")
    for field, value in update_in.dict(exclude_unset=True).items():
        setattr(exercise, field, value)
    db.commit()
    db.refresh(exercise)
    log_action(db, current_user.id, "update_exercise", "exercise", exercise.id)
    return exercise

# --- comment endpoints ---
@router.post("/exercises/{exercise_id}/comments", response_model=ExerciseCommentResponse, status_code=201)
def add_comment(
    exercise_id: int,
    comment_in: ExerciseCommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    exercise = db.query(Exercise).filter(Exercise.id == exercise_id).first()
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")
    if current_user.role != "Admin" and exercise.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Not permitted to comment on this exercise")
    comment = ExerciseComment(
        exercise_id=exercise_id,
        user_id=current_user.id,
        comment=comment_in.comment
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    log_action(db, current_user.id, "add_comment", "exercise_comment", comment.id)
    return comment

@router.get("/exercises/{exercise_id}/comments", response_model=List[ExerciseCommentResponse])
def list_comments(
    exercise_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    exercise = db.query(Exercise).filter(Exercise.id == exercise_id).first()
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")
    if current_user.role != "Admin" and exercise.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Not permitted to view comments for this exercise")
    comments = db.query(ExerciseComment).filter(ExerciseComment.exercise_id == exercise_id).all()
    return comments

# --- audit log endpoint (admin) ---
@router.get("/audit-logs", response_model=List[AuditLogResponse],
            dependencies=[Depends(require_role("Admin"))])
def list_audit_logs(db: Session = Depends(get_db)) -> Any:
    return db.query(AuditLog).order_by(AuditLog.timestamp.desc()).all()
