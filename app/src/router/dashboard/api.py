from __future__ import annotations
from fastapi import APIRouter, Depends, Form, HTTPException, Request, Cookie
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.router.user.crud import CRUDUser
from app.src.core.templates import get_templates
from app.src.core.session import get_async_session
from app.src.router.user_nutrition.crud import CRUDUserNutrition
from app.src.core.security import Hasher, TokenService, AuthService

router = APIRouter()
token_service = TokenService()
crud_user = CRUDUser()
auth_service = AuthService()
templates = get_templates()

async def require_admin_cookie(admin_access: str = Cookie(None)):
    if not admin_access:
        raise HTTPException(status_code=302, headers={"Location": "/dashboard/login"})
    try:
        payload = await auth_service._decode_token(admin_access)
        if payload.get("role") != "admin":
            raise HTTPException(status_code=302, headers={"Location": "/dashboard/login"})
        return payload
    except Exception:
        raise HTTPException(status_code=302, headers={"Location": "/dashboard/login"})

@router.get("/login")
async def login_page(request: Request, admin_access: str = Cookie(None)):
    if admin_access:
        try:
            payload = await auth_service._decode_token(admin_access)
            if payload.get("role") == "admin":
                return RedirectResponse(url="/dashboard/users", status_code=302)
        except Exception:
            pass
    return templates.TemplateResponse("admin/login.html", {"request": request})

@router.post("/login")
async def admin_login(
    email: str = Form(...),
    password: str = Form(...),
    session: AsyncSession = Depends(get_async_session),
):
    user = await crud_user.get_user_by_email(session=session, email=email)
    if not user or not Hasher.verify_password(password, user.password):
        return RedirectResponse(
            url="/dashboard/login?error=Invalid+email+or+password",
            status_code=302
        )

    if user.role != "admin":
        return RedirectResponse(
            url="/dashboard/login?error=Access+denied",
            status_code=302
        )

    payload = {"id": user.id, "role": user.role}
    access_token = token_service.generate_access_token(payload)

    res = RedirectResponse(url="/dashboard/users", status_code=302)
    res.set_cookie(
        key="admin_access",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=900
    )
    return res


@router.post("/logout")
async def admin_logout():
    res = RedirectResponse(url="/dashboard/login", status_code=302)
    res.delete_cookie("admin_access")
    return res

@router.get("/users")
async def users_page(request: Request, auth=Depends(require_admin_cookie), session: AsyncSession = Depends(get_async_session)):
    users = await crud_user.get_user_admin_by_id(session=session, id=auth.get("id"))
    return templates.TemplateResponse("admin/users.html", {"request": request, "users": users, "auth": auth})

@router.get("/users/{user_id}")
async def user_detail_page(
    request: Request,
    user_id: int,
    page: int = 1,
    limit: int = 10,
    auth=Depends(require_admin_cookie),
    session: AsyncSession = Depends(get_async_session),
):
    user = await crud_user.get_user_by_id(session=session, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    offset = (page - 1) * limit
    user_nutritions = await CRUDUserNutrition().get_list(
        session=session, user_id=user_id, limit=limit, offset=offset
    )

    total_records = len(user.user_nutritions) if user.user_nutritions else 0
    total_pages = (total_records + limit - 1) // limit

    return templates.TemplateResponse(
        "admin/user_detail.html",
        {
            "request": request,
            "user": user,
            "user_nutritions": user_nutritions,
            "page": page,
            "total_pages": total_pages,
            "limit": limit,
            "auth": auth,
        },
    )

