"""Authentication routes: login, register (admin), me"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from healthcare_backend.database import get_db
from healthcare_backend.models.user import User
from healthcare_backend.schemas.user import UserCreate, UserLogin, UserOut, Token
from healthcare_backend.auth.password import hash_password, verify_password
from healthcare_backend.auth.jwt_handler import create_access_token
from healthcare_backend.auth.dependencies import get_current_user, require_role

router = APIRouter(prefix="/auth", tags=["Authentication"])
logger = logging.getLogger("bcg.auth")


@router.post("/login", response_model=Token, summary="Login and receive JWT token")
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == credentials.username).first()
    if not user or not verify_password(credentials.password, user.password_hash):
        logger.warning(f"Failed login attempt for username: {credentials.username}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token({"sub": user.username, "role": user.role})
    logger.info(f"User logged in: {user.username} (role={user.role})")
    return Token(access_token=token, user=UserOut.model_validate(user))


@router.post(
    "/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user (admin only)",
)
def register(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    new_user = User(
        username=user_data.username,
        password_hash=hash_password(user_data.password),
        role=user_data.role,
        linked_patient_id=user_data.linked_patient_id,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    logger.info(f"New user registered: {new_user.username} by admin {current_user.username}")
    return new_user


@router.get("/me", response_model=UserOut, summary="Get current authenticated user")
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
