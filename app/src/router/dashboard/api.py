from __future__ import annotations
from datetime import datetime
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, Form, HTTPException, Request, Cookie

from app.src.router.user.crud import CRUDUser
from app.src.core.templates import get_templates
from app.src.core.session import get_async_session
from app.src.utils.email_client import EmailClient
from app.src.models.user_nutrition import UserNutrition
from app.src.router.user_nutrition.crud import CRUDUserNutrition
from app.src.core.security import Hasher, TokenService, AuthService

router = APIRouter()
templates = get_templates()
crud_user = CRUDUser()
email_client = EmailClient()
auth_service = AuthService()
token_service = TokenService()

def render_page(template, request, **context):
    context.setdefault("year", datetime.now().year)
    return templates.TemplateResponse(template, {"request": request, **context})

async def require_admin_cookie(admin_access: str = Cookie(None)):
    if not admin_access:
        return RedirectResponse("/dashboard/login")
    try:
        payload = await auth_service.decode_token(admin_access)
        if payload.get("role") != "admin":
            return RedirectResponse("/dashboard/login")
        return payload
    except Exception:
        return RedirectResponse("/dashboard/login")

@router.get("/login")
async def login_page(request: Request, admin_access: str = Cookie(None)):
    if admin_access:
        try:
            payload = await auth_service.decode_token(admin_access)
            if payload.get("role") == "admin":
                return RedirectResponse("/dashboard/users")
        except Exception:
            pass
    return render_page("admin/login.html", request)

@router.post("/login")
async def admin_login(
    email: str = Form(...),
    password: str = Form(...),
    session: AsyncSession = Depends(get_async_session),
):
    user = await crud_user.get_user_by_email(session, email)
    if not user or not Hasher.verify_password(password, user.password):
        return RedirectResponse("/dashboard/login?error=Invalid+credentials", status_code=302)
    if user.role != "admin":
        return RedirectResponse("/dashboard/login?error=Access+denied", status_code=302)

    payload = {"id": user.id, "role": user.role}
    token = token_service.generate_token(payload=payload, expires_in_hours=6)
    res = RedirectResponse("/dashboard/users", status_code=302)
    res.set_cookie("admin_access", token, httponly=True, secure=True, samesite="strict", max_age=21600)
    return res

@router.post("/logout")
async def admin_logout():
    res = RedirectResponse("/dashboard/login", status_code=302)
    res.delete_cookie("admin_access")
    return res

@router.get("/users")
async def users_page(request: Request, auth=Depends(require_admin_cookie), session: AsyncSession = Depends(get_async_session)):
    users = await crud_user.get_users(session=session)
    return render_page("admin/users.html", request, users=users, auth=auth)

@router.get("/users/{user_id}")
async def user_detail_page(
    request: Request,
    user_id: str,
    page: int = 1,
    limit: int = 10,
    sort: str = "created_at",
    order: str = "desc",
    auth=Depends(require_admin_cookie),
    session: AsyncSession = Depends(get_async_session),
):
    user = await crud_user.get_user_by_id(session, id=user_id)
    if not user:
        raise HTTPException(404, "User not found")

    offset = (page - 1) * limit

    valid_sorts = {
        "bmi": UserNutrition.bmi,
        "height": UserNutrition.height_cm,
        "weight": UserNutrition.weight_kg,
        "ideal": UserNutrition.ideal_weight_kg,
        "created_at": UserNutrition.created_at,
    }

    sort_column = valid_sorts.get(sort, UserNutrition.created_at)
    ordering = sort_column.desc() if order == "desc" else sort_column.asc()

    crud_nutrition = CRUDUserNutrition()
    nutritions = await crud_nutrition.get_list_sorted(
        session=session,
        user_id=user_id,
        limit=limit,
        offset=offset,
        ordering=ordering
    )

    total_records = await crud_nutrition.count_by_user(session, user_id)
    total_pages = (total_records + limit - 1) // limit

    return render_page(
        "admin/user_detail.html",
        request,
        user=user,
        user_nutritions=nutritions,
        page=page,
        total_pages=total_pages,
        limit=limit,
        auth=auth,
    )

@router.get("/reset/password")
async def reset_password_page(request: Request):
    return render_page("admin/reset_password.html", request)

@router.post("/reset/password")
async def send_reset_link(
    request: Request,
    email: str = Form(...),
    session: AsyncSession = Depends(get_async_session),
):
    user = await crud_user.get_user_by_email(session, email)
    if not user:
        return render_page("admin/reset_password.html", request, error="Email not found")

    payload = {"id": user.id, "email": user.email}
    token = token_service.generate_token(payload=payload, token_type="reset_password", expires_in_minutes=30)
    reset_link = f"https://sehatiapps.web.id/dashboard/reset/password/confirm?token={token}"
    email_client.send_password_reset_email(recipient=user.email, fullname=user.fullname, link=reset_link)
    return render_page("admin/reset_password.html", request, success="Link sent to your email.")

@router.get("/reset/password/confirm")
async def confirm_reset_password(request: Request, token: str):
    return render_page("admin/reset_confirm.html", request, token=token)

@router.post("/reset/password/confirm")
async def confirm_reset_password_post(
    request: Request,
    token: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    session: AsyncSession = Depends(get_async_session),
):
    if new_password != confirm_password:
        return render_page("admin/reset_confirm.html", request, token=token, error="Passwords do not match.")

    try:
        payload = await auth_service._decode_token(token)
        if payload.get("type") != "reset_password":
            raise ValueError("Invalid token type.")
        user_id = payload.get("id")
    except Exception:
        return render_page("admin/reset_password.html", request, error="Invalid or expired token.")

    user = await crud_user.get_user_admin_by_id(session, user_id)
    if not user:
        return render_page("admin/reset_password.html", request, error="User not found.")

    try:
        user.password = Hasher.hash_password(new_password)
        await session.commit()
    except Exception:
        await session.rollback()
        return render_page("admin/reset_confirm.html", request, error="Database error. Try again later.")

    return render_page("admin/reset_success.html", request, message="Password successfully updated.")