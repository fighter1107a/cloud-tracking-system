from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from backend.app.auth import (
    verify_password,
    create_access_token,
    get_current_admin,
    seed_default_admin
)
from backend.app.config import settings
from backend.app.database import get_db
from backend.app.models import AdminUser
from backend.app.schemas import Token, AdminUserResponse, AdminLoginRequest

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/login", response_model=Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Authenticate administrator credentials and return an authorized JWT bearer token.
    Compatible with Swagger UI OAuth2 password flow.
    """
    admin = db.query(AdminUser).filter(AdminUser.username == form_data.username).first()
    if not admin or not verify_password(form_data.password, admin.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive admin account"
        )
        
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    user_role = getattr(admin, "role", "ADMIN") or "ADMIN"
    access_token = create_access_token(
        data={"sub": admin.username, "role": user_role},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", "role": user_role}

@router.post("/login-json", response_model=Token)
def login_with_json(
    credentials: AdminLoginRequest,
    db: Session = Depends(get_db)
):
    """
    Alternative JSON login endpoint for modern frontend fetch / AJAX requests.
    """
    admin = db.query(AdminUser).filter(AdminUser.username == credentials.username).first()
    if not admin or not verify_password(credentials.password, admin.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive admin account"
        )
        
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    user_role = getattr(admin, "role", "ADMIN") or "ADMIN"
    access_token = create_access_token(
        data={"sub": admin.username, "role": user_role},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", "role": user_role}

@router.get("/me", response_model=AdminUserResponse)
def read_current_admin(current_admin: AdminUser = Depends(get_current_admin)):
    """Return currently authenticated administrator profile."""
    return current_admin
