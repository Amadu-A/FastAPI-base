# /base_app/views/web.py
from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Annotated, Optional

from fastapi import APIRouter, Request, Depends, UploadFile, File, Form, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from base_app.core.logging import get_logger
from base_app.core.models import db_helper
from base_app.crud.user_repository import UserRepository, get_all_users

router = APIRouter()
log = get_logger("web")

TEMPLATES_DIR = Path(__file__).resolve().parents[2] / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

STATIC_DIR = Path(__file__).resolve().parents[2] / "static"
AVATAR_DIR = STATIC_DIR / "uploads" / "avatars"
AVATAR_DIR.mkdir(parents=True, exist_ok=True)


@router.get("/", name="home")
async def index_html(request: Request):
    """
    Главная страница.
    Имя роута — 'home', т.к. оно используется в templates/core/_header.html.
    """
    log.info({"event": "open_page", "path": "/", "method": "GET"})
    return templates.TemplateResponse("core/index.html", {"request": request})


@router.get("/users/", name="users_list_html")
async def users_list_html(
    request: Request,
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
):
    """
    HTML-страница со списком пользователей.
    """
    users = await get_all_users(session=session)
    log.info({"event": "open_page", "path": "/users/", "method": "GET", "count": len(users)})
    return templates.TemplateResponse("users/list.html", {"request": request, "users": users})


def _require_logged_in(request: Request) -> Optional[str]:
    """
    Возвращает email пользователя из сессии, если он залогинен, иначе None.
    """
    token = request.session.get("access_token")
    email = request.session.get("user_email")
    if not token or not email:
        return None
    return email


@router.get("/profile", name="profile_html")
async def profile_html(
    request: Request,
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
):
    """
    Профиль пользователя (форма редактирования).
    """
    email = _require_logged_in(request)
    if not email:
        return RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER)

    repo = UserRepository()
    user = await repo.get_by_email(session, email=email)
    if not user:
        return RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER)

    profile = await repo.get_profile_by_user_id(session, user_id=user.id)
    return templates.TemplateResponse("core/profile.html", {"request": request, "user": user, "profile": profile})


@router.post("/profile", name="profile_post_html")
async def profile_post_html(
    request: Request,
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
    nickname: Annotated[str | None, Form()] = None,
    first_name: Annotated[str | None, Form()] = None,
    second_name: Annotated[str | None, Form()] = None,
    phone: Annotated[str | None, Form()] = None,
    email_field: Annotated[str | None, Form()] = None,  # поле email профиля (не user.email)
    tg_id: Annotated[str | None, Form()] = None,
    tg_nickname: Annotated[str | None, Form()] = None,
    session_str: Annotated[str | None, Form()] = None,
    avatar: Annotated[UploadFile | None, File()] = None,
):
    """
    Обработка формы профиля. Поддерживает обновление полей и загрузку аватара.
    """
    email = _require_logged_in(request)
    if not email:
        return RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER)

    repo = UserRepository()
    user = await repo.get_by_email(session, email=email)
    if not user:
        return RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER)

    profile = await repo.get_profile_by_user_id(session, user_id=user.id)
    if not profile:
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

    updates: dict[str, object] = {}
    for key, val in [
        ("nickname", nickname),
        ("first_name", first_name),
        ("second_name", second_name),
        ("phone", phone),
        ("email", email_field),
        ("tg_id", tg_id),
        ("tg_nickname", tg_nickname),
        ("session", session_str),
    ]:
        if val is not None:
            updates[key] = val.strip() if isinstance(val, str) else val

    # загрузка аватара
    if avatar and avatar.filename:
        ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        ext = os.path.splitext(avatar.filename)[1].lower()[:8]
        filename = f"user_{user.id}_{ts}{ext or '.bin'}"
        dst = AVATAR_DIR / filename
        content = await avatar.read()
        dst.write_bytes(content)
        updates["avatar"] = f"uploads/avatars/{filename}"  # путь относительно /static

    if updates:
        await repo.update_profile(session, profile_id=profile.id, **updates)
        await session.commit()

    return RedirectResponse(url="/profile", status_code=status.HTTP_303_SEE_OTHER)
