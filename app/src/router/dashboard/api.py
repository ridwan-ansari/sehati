from __future__ import annotations
import re
from loguru import logger
from datetime import datetime
from zoneinfo import ZoneInfo
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, Form, HTTPException, Request, Cookie, UploadFile

from app.src.core.config import settings
from app.src.router.user.crud import CRUDUser
from app.src.core.templates import get_templates
from app.src.router.recipe.crud import CRUDRecipe
from app.src.core.session import get_async_session
from app.src.utils.email_client import EmailClient
from app.src.router.merchandise.crud import crud_merch
from app.src.models.user_nutrition import UserNutrition
from app.src.router.merchandise.crud import crud_merch_claim
from app.src.utils.file_service import save_upload_with_uuid
from app.src.router.user_nutrition.crud import CRUDUserNutrition
from app.src.utils.point_service import redeem_merchandise_points
from app.src.router.point.crud import crud_wallet, crud_transaction
from app.src.core.security import Hasher, TokenService, AuthService

router = APIRouter()
crud_user = CRUDUser()
crud_recipe = CRUDRecipe()
templates = get_templates()
email_client = EmailClient()
auth_service = AuthService()
token_service = TokenService()

def render_page(template, request, **context):
    context.setdefault("year", datetime.now().year)
    return templates.TemplateResponse(template, {"request": request, **context})

async def require_admin_cookie(admin_access: str = Cookie(None)):
    if not admin_access:
        raise HTTPException(
            status_code=302,
            detail="Unauthorized",
            headers={"Location": "/dashboard/login?error=Unauthorized"}
        )
    try:
        payload = await auth_service._decode_token(admin_access)
        if payload.get("role") != "admin":
            raise HTTPException(
                status_code=302,
                detail="Access denied",
                headers={"Location": "/dashboard/login?error=Access+denied"}
            )
        return payload
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=302,
            detail="Session expired",
            headers={"Location": "/dashboard/login?error=Session+expired"}
        )

@router.get("/login")
async def login_page(request: Request, admin_access: str = Cookie(None)):
    if admin_access:
        try:
            payload = await auth_service._decode_token(admin_access)
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
    limit: int = 5,
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

    for n in nutritions:
        n.created_at = n.created_at.astimezone(ZoneInfo("Asia/Jakarta"))

    all_nutritions_raw = await crud_nutrition.get_list(session, user_id)

    all_nutritions = [
        {
            "created_at": n.created_at.strftime("%Y-%m-%d"),
            "weight_kg": n.weight_kg,
            "ideal_weight_kg": n.ideal_weight_kg,
        }
        for n in all_nutritions_raw
    ]

    total_records = await crud_nutrition.count_by_user(session, user_id)
    total_pages = (total_records + limit - 1) // limit

    return render_page(
        "admin/user_detail.html",
        request,
        user=user,
        user_nutritions=nutritions,
        all_nutritions=all_nutritions,
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
    try:
        email_client.send_password_reset_email(recipient=user.email, fullname=user.fullname, link=reset_link)
    except Exception as error:
        logger.error(error)
        return render_page("admin/reset_password.html", request, error="Something was wrong. Please try again later.")
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
        if re.fullmatch(settings.PASSWORD_REGEX, new_password) is None:
            raise ValueError("Password must be at least 8 chars, contain upper, lower, digit, and symbol.")
        user.password = Hasher.hash_password(new_password)
        await session.commit()
    except Exception:
        await session.rollback()
        return render_page("admin/reset_confirm.html", request, error="Database error. Try again later.")

    return render_page("admin/reset_success.html", request, message="Password successfully updated.")

@router.get("/recipes")
async def recipes_page(
    request: Request,
    page: int = 1,
    limit: int = 10,
    auth=Depends(require_admin_cookie),
    session: AsyncSession = Depends(get_async_session),
):
    offset = (page - 1) * limit

    recipes = await crud_recipe.get_all(session, limit=limit, offset=offset)
    total = await crud_recipe.count(session)
    total_pages = (total + limit - 1) // limit

    return render_page(
        "admin/recipes.html",
        request,
        recipes=recipes,
        page=page,
        total_pages=total_pages,
        limit=limit,
        auth=auth,
    )

@router.get("/recipes/upload")
async def recipe_upload_page(
    request: Request,
    auth=Depends(require_admin_cookie)
):
    return render_page("admin/recipe_upload.html", request, auth=auth)

@router.post("/recipes/upload")
async def recipe_upload(
    request: Request,
    title: str = Form(...),
    description: str = Form(...),
    category: str = Form(None),
    file: UploadFile = Form(...),
    image: UploadFile = Form(None),
    session: AsyncSession = Depends(get_async_session),
    auth=Depends(require_admin_cookie),
):
    file_url = await save_upload_with_uuid(file, folder="recipe")
    image_url = await save_upload_with_uuid(image, folder="recipe")

    await crud_recipe.create(
        session=session,
        data={
            "title": title,
            "description": description,
            "file_url": f"/media/recipe/{file_url}",
            "image_url": f"/media/recipe/{image_url}",
            "category": category,
        }
    )

    return RedirectResponse("/dashboard/recipes", status_code=302)

@router.get("/leaderboard")
async def leaderboard_page(
    request: Request,
    auth=Depends(require_admin_cookie),
    session: AsyncSession = Depends(get_async_session)
):
    wallets = await crud_wallet.get_all(session=session)
    data = [
        {
            "nickname": w.user.nickname,
            "fullname": w.user.fullname,
            "achievement_points": w.achievement_points,
            "credit_points": w.credit_points,
        }
        for w in wallets
    ]

    return render_page("admin/leaderboard.html", request, leaderboard=data, auth=auth)

@router.get("/merchandise/upload")
async def recipe_upload_page(
    request: Request,
    auth=Depends(require_admin_cookie)
):
    return render_page("admin/merchandise_upload.html", request, auth=auth)

@router.post("/merchandise/upload")
async def merchandise_upload(
    request: Request,
    name: str = Form(...),
    description: str = Form(None),
    price_points: int = Form(...),
    stock: int = Form(...),
    image: UploadFile = Form(...),
    session: AsyncSession = Depends(get_async_session),
    auth=Depends(require_admin_cookie),
):
    image_url = await save_upload_with_uuid(image, folder="merchandise")

    await crud_merch.create(
        session=session,
        data={
            "name": name,
            "description": description,
            "price_points": price_points,
            "stock": stock,
            "image_url": f"/media/merchandise/{image_url}",
        }
    )

    return RedirectResponse("/dashboard/merchandise", status_code=302)

@router.get("/merchandise")
async def merchandise_page(
    request: Request,
    page: int = 1,
    limit: int = 10,
    success: str = None,
    error: str = None,
    auth=Depends(require_admin_cookie),
    session: AsyncSession = Depends(get_async_session),
):
    offset = (page - 1) * limit

    merch = await crud_merch.get_all(session, limit=limit, offset=offset)
    total = await crud_merch.count(session)
    total_pages = (total + limit - 1) // limit

    return render_page(
        "admin/merchandise.html",
        request,
        merch=merch,
        page=page,
        total_pages=total_pages,
        limit=limit,
        auth=auth,
        success=success,
        error=error,
    )

@router.post("/merchandise/update/{merch_id}")
async def update_merchandise(
    merch_id: str,
    name: str = Form(...),
    price_points: int = Form(...),
    stock: int = Form(...),
    session: AsyncSession = Depends(get_async_session),
    auth=Depends(require_admin_cookie)
):
    merchandise = await crud_merch.get_by_id(session=session, id=merch_id)
    if not merchandise:
        return RedirectResponse(
            "/dashboard/merchandise?error=Merchandise not found",
            status_code=302
        )

    merchandise.name = name
    merchandise.price_points = price_points
    merchandise.stock = stock

    await session.commit()
    await session.refresh(merchandise)

    return RedirectResponse(
        "/dashboard/merchandise?success=Updated successfully",
        status_code=302
    )

@router.get("/merchandise/claims")
async def merchandise_claims_page(
    request: Request,
    page: int = 1,
    limit: int = 10,
    error: str = None,
    success: str = None,
    auth=Depends(require_admin_cookie),
    session: AsyncSession = Depends(get_async_session),
):
    offset = (page - 1) * limit

    claims = await crud_merch_claim.get_list(session=session, limit=limit, offset=offset)
    total = await crud_merch_claim.count(session=session)
    total_pages = (total + limit - 1) // limit

    return render_page(
        "admin/merch_claims.html",
        request,
        claims=claims,
        page=page,
        total_pages=total_pages,
        limit=limit,
        auth=auth,
        success=success,
        error=error
    )

@router.post("/merchandise/claims/{claim_id}/approve")
async def approve_claim(claim_id: str, session: AsyncSession = Depends(get_async_session), auth=Depends(require_admin_cookie)):
    merchandise_claim = await crud_merch_claim.get_by_id(id=claim_id, session=session)
    merchandise = merchandise_claim.merchandise

    if merchandise.stock <= 0:
        return RedirectResponse(
            "/dashboard/merchandise/claims?error=Stock+unavailable+Please+add+stock+on+the+merchandise+list+page+or+reject+this+claim",
            status_code=302
        )
    
    user = await crud_user.get_user_by_id(session=session, id=merchandise_claim.user_id)
    await crud_merch_claim.update_status(session, claim_id=claim_id, status="approved")
    await crud_merch.update_stock(session=session, id=merchandise_claim.merchandise_id)
    await redeem_merchandise_points(session=session, user_id=user.id, merchandise_id=merchandise.id)

    try:
        email_client.send_approve_claim_marchandise(
            recipient=user.email,
            context={
                "fullname": user.fullname,
                "merchandise_name": merchandise_claim.merchandise.name,
                "year": datetime.now().year
            }
        )
    except Exception as error:
        logger.error(error)

    return RedirectResponse("/dashboard/merchandise/claims?success=Approved", status_code=302)

@router.post("/merchandise/claims/{claim_id}/reject")
async def reject_claim(claim_id: str, session: AsyncSession = Depends(get_async_session), auth=Depends(require_admin_cookie)):
    merchandise_claim = await crud_merch_claim.get_by_id(id=claim_id, session=session)

    if not merchandise_claim:
        return RedirectResponse("/dashboard/merchandise/claims?error=Claim+not+found", status_code=302)

    if merchandise_claim.status != "pending":
        return RedirectResponse("/dashboard/merchandise/claims?error=Claim+already+processed", status_code=302)

    user = await crud_user.get_user_by_id(session=session, id=merchandise_claim.user_id)
    await crud_merch_claim.update_status(session, claim_id=claim_id, status="rejected")

    try:
        email_client.send_rejected_claim_marchandise(
            recipient=user.email,
            context={
                "fullname": user.fullname,
                "merchandise_name": merchandise_claim.merchandise.name,
                "year": datetime.now().year,
            }
        )
    except Exception as error:
        logger.error(error)

    return RedirectResponse("/dashboard/merchandise/claims?success=Claim+has+been+rejected", status_code=302)

@router.get("/transactions")
async def point_transactions_page(
    request: Request,
    name: str = None,
    page: int = 1,
    limit: int = 20,
    auth=Depends(require_admin_cookie),
    session: AsyncSession = Depends(get_async_session)
):
    offset = (page - 1) * limit

    transactions = await crud_transaction.get_history(session, name=name, limit=limit, offset=offset)
    for t in transactions:
        t.created_at = t.created_at.astimezone(ZoneInfo("Asia/Jakarta"))
    total = await crud_transaction.count(session, name=name)
    total_pages = (total + limit - 1) // limit

    return render_page(
        "admin/point_transactions.html",
        request,
        transactions=transactions,
        name=name,
        page=page,
        limit=limit,
        total_pages=total_pages,
        auth=auth,
    )
