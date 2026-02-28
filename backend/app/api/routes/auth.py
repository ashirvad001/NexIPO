from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.database import get_db
from app.services.auth_service import AuthService
from app.schemas.user import UserCreate, UserResponse, Token

settings = get_settings()

router = APIRouter(tags=["Auth"]) 

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = AuthService.decode_token(token)
    user_id = payload.get("sub") or payload.get("user_id")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user = AuthService.get_user_by_id(db, int(user_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


@router.post("/auth/signup", response_model=Token)
def signup(user_in: UserCreate, db: Session = Depends(get_db)) -> Any:
    user = AuthService.create_user(db, user_in)
    access_token = AuthService.create_access_token({"sub": str(user.id), "email": user.email})
    return {"access_token": access_token, "token_type": "bearer", "user": user}


@router.post("/auth/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = AuthService.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect credentials")
    access_token = AuthService.create_access_token({"sub": str(user.id), "email": user.email})
    return {"access_token": access_token, "token_type": "bearer", "user": user}


@router.post("/auth/login/json", response_model=Token)
def login_json(payload: dict, db: Session = Depends(get_db)):
    identifier = payload.get("identifier") or payload.get("email")
    password = payload.get("password")
    user = AuthService.authenticate_user(db, identifier, password)
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect credentials")
    access_token = AuthService.create_access_token({"sub": str(user.id), "email": user.email})
    return {"access_token": access_token, "token_type": "bearer", "user": user}


@router.get("/auth/me", response_model=UserResponse)
def read_current_user(current_user=Depends(get_current_user)):
    return current_user


@router.put("/auth/me", response_model=UserResponse)
def update_profile(data: dict, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    # simple partial update
    from app.schemas.user import UserUpdate
    user_update = UserUpdate(**data)
    updated = AuthService.update_user(db, current_user.id, user_update)
    return updated


@router.post("/auth/change-password")
def change_password(data: dict, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    current_password = data.get("current_password")
    new_password = data.get("new_password")
    AuthService.change_password(db, current_user.id, current_password, new_password)
    return {"detail": "Password changed"}


@router.post("/auth/logout")
def logout(current_user=Depends(get_current_user)):
    # No-op for JWT (client should discard token). Keep endpoint for compatibility.
    return {"detail": "Logged out"}


@router.delete("/auth/me")
def delete_account(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    AuthService.delete_user(db, current_user.id)
    return {"detail": "Account deactivated"}
