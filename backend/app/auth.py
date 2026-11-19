from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
import bcrypt
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.database import get_db
from backend.app.models import AdminUser

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    # Truncate password to 72 bytes if necessary per bcrypt algorithm limits
    pwd_bytes = password.encode('utf-8')[:72]
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(pwd_bytes, salt).decode('utf-8')

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def get_current_admin(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> AdminUser:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials or token expired",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    admin = db.query(AdminUser).filter(AdminUser.username == username).first()
    if admin is None or not admin.is_active:
        raise credentials_exception
    return admin

def require_admin(current_user: AdminUser = Depends(get_current_admin)) -> AdminUser:
    """RBAC Guard: Enforces that the authenticated user holds the ADMIN role."""
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: Only administrators can create or delete shipments."
        )
    return current_user

def require_staff(current_user: AdminUser = Depends(get_current_admin)) -> AdminUser:
    """RBAC Guard: Allows access to either ADMIN or DELIVERY_AGENT."""
    if current_user.role not in ["ADMIN", "DELIVERY_AGENT"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: Authorized staff credentials required."
        )
    return current_user

def seed_default_admin(db: Session) -> AdminUser:
    """Ensures default administrator and delivery agent accounts exist upon startup."""
    # 1. Administrator account
    admin = db.query(AdminUser).filter(AdminUser.username == settings.DEFAULT_ADMIN_USERNAME).first()
    if not admin:
        admin = AdminUser(
            username=settings.DEFAULT_ADMIN_USERNAME,
            hashed_password=get_password_hash(settings.DEFAULT_ADMIN_PASSWORD),
            role="ADMIN",
            is_active=True
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
    elif not admin.role:
        admin.role = "ADMIN"
        db.commit()

    # 2. Delivery Boy / Agent account
    delivery = db.query(AdminUser).filter(AdminUser.username == "delivery").first()
    if not delivery:
        delivery = AdminUser(
            username="delivery",
            hashed_password=get_password_hash("Delivery@2026"),
            role="DELIVERY_AGENT",
            is_active=True
        )
        db.add(delivery)
        db.commit()
    elif not delivery.role:
        delivery.role = "DELIVERY_AGENT"
        db.commit()

    return admin
