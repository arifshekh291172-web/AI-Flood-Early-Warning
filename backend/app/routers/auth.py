from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models.core import User, AuditLog
from backend.app.schemas.auth import LoginRequest, TokenResponse, UserProfile
from backend.app.utils.security import verify_password, create_access_token, get_current_user
from backend.app.config import settings

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/login", response_model=TokenResponse)
def login(creds: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == creds.email).first()
    if not user or not verify_password(creds.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account has been disabled. Contact system administrator."
        )

    token = create_access_token(subject=user.id, role=user.role.name)

    # Record login in audit log
    audit = AuditLog(
        user_id=user.id,
        user_email=user.email,
        action="USER_LOGIN",
        resource_type="auth",
        resource_id=user.id,
        result_status="SUCCESS"
    )
    db.add(audit)
    db.commit()

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role.name,
        department=user.department,
        state_jurisdiction=user.state_jurisdiction
    )

@router.get("/me", response_model=UserProfile)
def get_current_user_profile(user: User = Depends(get_current_user)):
    return UserProfile(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role.name,
        phone=user.phone,
        department=user.department,
        state_jurisdiction=user.state_jurisdiction,
        is_active=user.is_active
    )
