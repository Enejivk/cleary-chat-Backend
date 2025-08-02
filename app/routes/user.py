from sqlalchemy.orm import Session
from fastapi import APIRouter, HTTPException, Depends
from app.db.session import get_db
from app.models.models import User
from app.schemas import UserCreate, UserProfileUpdate
from app.schemas.user_schema import Token, UserOut
from app.utils import authenticate_user, create_access_token, get_current_user, get_password_hash
from app.utils.auth import get_current_user_from_db
from app.setting import current_config
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from typing import Annotated
from fastapi import status

router = APIRouter()

@router.post("/login", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db)
) -> Token:
    
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token with user ID as subject
    access_token_expires = timedelta(minutes=current_config.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.id}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")


@router.get("/auth/me", response_model=UserOut)
async def read_users_me(
    user_id: Annotated[str, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    user = await get_current_user_from_db(user_id, db)
    return user
    

@router.post("/register", response_model=UserOut)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    # Check if user with this email already exists
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Verify that passwords match
    if user.password != user.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match"
        )
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    db_user = User(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.put("/profile", response_model=UserOut)
async def update_user_profile(
    profile_data: UserProfileUpdate,
    user_id: Annotated[str, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    current_user = await get_current_user_from_db(user_id, db)
    if profile_data.name is not None:
        current_user.name = profile_data.name
    if profile_data.bio is not None:
        current_user.bio = profile_data.bio
    db.commit()
    db.refresh(current_user)
    return current_user