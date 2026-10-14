from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.deps import AuthContext
from app.auth.jwt import create_access_token, verify_password
from app.db.models import User
from app.schemas import LoginResponse, UserProfile


class InvalidCredentials(Exception):
    pass


def profile_from_auth(auth: AuthContext) -> UserProfile:
    return UserProfile(
        id=str(auth.user_id),
        email=auth.email,
        display_name=auth.display_name,
        tenant_id=str(auth.tenant_id),
        tenant_name=auth.tenant_name,
    )


async def login(db: AsyncSession, email: str, password: str) -> LoginResponse:
    result = await db.execute(
        select(User).options(selectinload(User.tenant)).where(User.email == email)
    )
    user = result.scalar_one_or_none()
    if user is None or not verify_password(password, user.password_hash):
        raise InvalidCredentials()
    token = create_access_token(user_id=user.id, tenant_id=user.tenant_id, email=user.email)
    profile = UserProfile(
        id=str(user.id),
        email=user.email,
        display_name=user.display_name,
        tenant_id=str(user.tenant_id),
        tenant_name=user.tenant.name,
    )
    return LoginResponse(access_token=token, user=profile)
