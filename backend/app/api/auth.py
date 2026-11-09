from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta

from app.database.session import get_db
from app.core.config import settings
from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.dependencies import get_current_user
from app.models.all_models import User, UserRole
from app.schemas.all_schemas import UserRegister, UserLogin, UserResponse, Token

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(user_in: UserRegister, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists."
        )

    # Validate role
    role_val = user_in.role.upper() if user_in.role else UserRole.TEAM_MEMBER.value
    valid_roles = [r.value for r in UserRole]
    if role_val not in valid_roles:
        role_val = UserRole.TEAM_MEMBER.value

    hashed_pw = get_password_hash(user_in.password)
    user = User(
        name=user_in.name.strip(),
        email=user_in.email.strip().lower(),
        password_hash=hashed_pw,
        role=role_val,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id), "role": user.role})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user
    }

@router.post("/login", response_model=Token)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == login_data.email.strip().lower()).first()
    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account is deactivated. Please contact administrator."
        )

    token = create_access_token({"sub": str(user.id), "role": user.role})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user
    }

@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    return current_user

