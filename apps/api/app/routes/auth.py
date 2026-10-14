from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import AuthContext, get_current_user
from app.db.session import get_db
from app.schemas import LoginRequest, LoginResponse, UserProfile
from app.services.auth import InvalidCredentials, login, profile_from_auth

router = APIRouter(prefix="/v1/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login_route(body: LoginRequest, db: AsyncSession = Depends(get_db)) -> LoginResponse:
    try:
        return await login(db, body.email, body.password)
    except InvalidCredentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        ) from None


@router.get("/me", response_model=UserProfile)
async def me(auth: AuthContext = Depends(get_current_user)) -> UserProfile:
    return profile_from_auth(auth)
