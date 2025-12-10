# /base_app/crud/user_repository.py
from __future__ import annotations

from typing import Optional, Sequence

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from base_app.core.logging import get_logger
from base_app.core.models import User, Profile, Permission
from base_app.core.schemas.user import UserCreate
from base_app.core.security import hash_password

log = get_logger("repo.user")


class UserRepository:
    """
    Репозиторий для User/Profile/Permission.
    """

    async def get_by_email(self, session: AsyncSession, *, email: str) -> Optional[User]:
        log.info({"event": "get_by_email", "email": email})
        res = await session.execute(
            select(User)
            .options(selectinload(User.profile))  # <— eager-load профиля
            .where(User.email == email)
        )
        return res.scalar_one_or_none()

    async def create_user_with_profile_and_permission(
        self,
        session: AsyncSession,
        *,
        email: str,
        hashed_password: str,
    ) -> User:
        log.info({"event": "create_user_start", "email": email})

        user = User(email=email, hashed_password=hashed_password, is_active=True)
        session.add(user)
        await session.flush()  # user.id

        log.info({"event": "create_profile", "user_id": user.id})
        profile = Profile(user_id=user.id, email=email, verification=False)
        session.add(profile)
        await session.flush()  # profile.id

        log.info({"event": "create_permission", "profile_id": profile.id})
        perm = Permission(
            profile_id=profile.id,
            is_superadmin=False,
            is_admin=False,
            is_staff=False,
            is_updater=False,
            is_reader=False,
            is_user=True,
        )
        session.add(perm)
        await session.flush()

        log.info({"event": "create_user_done", "user_id": user.id})
        return user

    async def get_profile_by_user_id(self, session: AsyncSession, *, user_id: int) -> Optional[Profile]:
        res = await session.execute(select(Profile).where(Profile.user_id == user_id))
        return res.scalar_one_or_none()

    async def update_profile(
        self,
        session: AsyncSession,
        *,
        profile_id: int,
        **fields,
    ) -> None:
        # Обновляем только переданные поля
        await session.execute(
            update(Profile)
            .where(Profile.id == profile_id)
            .values(**fields)
        )
        await session.flush()


# ---- вспомогательные функции (используются REST / views) ----
async def get_all_users(session: AsyncSession) -> Sequence[User]:
    log.info({"event": "list_users"})
    res = await session.execute(select(User).order_by(User.id.desc()))
    return list(res.scalars())


async def create_user(session: AsyncSession, user_create: UserCreate) -> User:
    repo = UserRepository()
    email = user_create.email.strip().lower()
    if await repo.get_by_email(session, email=email):
        log.info({"event": "create_user_exists", "email": email})
        raise ValueError("email_already_exists")

    user = await repo.create_user_with_profile_and_permission(
        session,
        email=email,
        hashed_password=hash_password(user_create.password),
    )
    return user
