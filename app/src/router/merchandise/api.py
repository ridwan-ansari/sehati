from __future__ import annotations
from loguru import logger
from datetime import datetime
from fastapi import APIRouter, Depends, Form
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.core.security import AuthService
from app.src.router.user.crud import crud_user
from app.src.router.point.crud import crud_wallet
from app.src.core.session import get_async_session
from app.src.utils.handler import response_handler
from app.src.utils.email_client import email_client
from app.src.utils.i18n import get_lang, t
from app.src.router.merchandise.crud import crud_merch, crud_merch_claim

router = APIRouter()
auth_service = AuthService()


@router.get("/")
async def get_merchandise(
    name: str = None,
    limit: int = 20,
    offset: int = 0,
    session: AsyncSession = Depends(get_async_session),
    authentication: dict = Depends(auth_service.require_access_token),
    lang: str = Depends(get_lang),
):
    with response_handler() as response:
        response.status_code = 200
        response.message = t("merchandise_list_success", lang)
        response.data = await crud_merch.get_all_with_claim_status(
            session=session, name=name, limit=limit, offset=offset, user_id=authentication.get("id")
        )
    return response.build()


@router.post("/claim")
async def claim_merchandise(
    merchandise_id: str = Form(...),
    session: AsyncSession = Depends(get_async_session),
    authentication: dict = Depends(auth_service.require_access_token),
    lang: str = Depends(get_lang),
):
    with response_handler() as response:
        user_id = authentication.get("id")
        admin = await crud_user.get_admin_user(session=session)
        user = await crud_user.get_user_by_id(session=session, id=user_id)
        merchandise = await crud_merch.get_by_id(id=merchandise_id, session=session)
        wallet = await crud_wallet.get_by_user(session=session, user_id=user_id)
        if wallet.credit_points < merchandise.price_points:
            raise ValueError(t("insufficient_points", lang))
        await crud_merch_claim.create(session=session, user_id=user_id, merchandise_id=merchandise_id, lang=lang)
        try:
            email_client.send_claim_marchandise_notification(
                recipient=admin.email,
                context={
                    "user_name": user.fullname,
                    "nickname": user.nickname,
                    "merchandise_name": merchandise.name,
                    "user_points": wallet.credit_points,
                    "merchandise_price": merchandise.price_points,
                    "year": datetime.now().year,
                },
            )
        except Exception as error:
            logger.error(error)
        response.status_code = 201
        response.message = t("claim_sent_to_admin", lang)
    return response.build()
