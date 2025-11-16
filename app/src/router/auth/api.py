from __future__ import annotations
from random import randint
from json import loads, dumps
from datetime import datetime
from fastapi import Depends, APIRouter, Form
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.models.user import User
from app.src.utils.redis_client import redis
from app.src.router.user.crud import CRUDUser 
from app.src.utils.email_client import EmailClient 
from app.src.utils.handler import response_handler
from app.src.core.session import get_async_session
from app.src.router.point.crud import CRUDPointWallet
from app.src.router.user.schema import UserRegisterSchema
from app.src.utils.execeptions import UnauthorizedException
from app.src.core.security import Hasher, TokenService, AuthService 

router = APIRouter()
crud_user = CRUDUser()
auth_service = AuthService()
email_client = EmailClient()
token_service = TokenService()
crud_wallet = CRUDPointWallet()

@router.post("/register")
async def register(user: UserRegisterSchema, session: AsyncSession = Depends(get_async_session)):
    with response_handler() as response:
        existing_user_email = await crud_user.get_user_by_email(session=session, email=user.email)
        existing_nickname = await crud_user.get_user_by_nickname(session=session, nickname=user.nickname)
        if existing_user_email:
            raise ValueError("Email is already registered. Please use another email.")
        if existing_nickname:
            raise ValueError("Nickname is already registered. Please use another nickname.")
        if user.picture and "/media/avatars/" not in user.picture:
            raise ValueError("The format picture is wrong, please check again.")
        user.password = Hasher.hash_password(user.password)
        code = randint(100000,999999)
        await redis.set(f"user:verify:{user.email}:{code}", value=user.model_dump_json(), ex=3600)
        email_client.send_verification_email(recipient=user.email, code=code)
        response.status_code = 201
        response.message = "Account registered successfully."
        response.data = {"email": user.email}
    return response.build()

@router.post("/login")
async def login(email: str = Form(...), password: str = Form(...), session: AsyncSession = Depends(get_async_session)):
    with response_handler() as response:
        user = await crud_user.get_user_by_email(session=session, email=email)
        if not user or not Hasher.verify_password(password, user.password):
            raise ValueError("Your email or password is incorrect. Please check and try again.")
        payload = {"id": user.id, "role": user.role}
        tokens = {
            "access_token": token_service.generate_token(payload=payload, token_type="access", expires_in_hours=12),
            "refresh_token": token_service.generate_token(payload=payload, token_type="refresh", expires_in_hours=24)
        }
        response.data = tokens
        response.status_code = 200
        response.message = "Successfully logged in."
    return response.build()

@router.post("/refresh")
async def login(authentication: dict = Depends(auth_service.require_refresh_token), session: AsyncSession = Depends(get_async_session)):
    with response_handler() as response:
        user = await CRUDUser().get_user_by_id(session=session, id=authentication.get("id"))
        if not user:
            raise UnauthorizedException("Invalid or expired token")
        
        payload = {"id": user.id, "role": user.role}
        tokens = {
            "access_token": token_service.generate_token(payload=payload, token_type="access", expires_in_hours=12)
        }
        response.data = tokens
        response.status_code = 200
        response.message = "Successfully logged in."
    return response.build()

@router.post("/verify/account")
async def verify(email: str, code: str, session: AsyncSession = Depends(get_async_session)):
    with response_handler() as response:
        key = f"user:verify:{email}:{code}"
        user = await redis.get(key)
        if not user:
            raise ValueError("Invalid verification code. Please enter the correct one and try again.")
        user = loads(user)
        date_of_birth = user.get("date_of_birth")
        user["verified"] = True
        if date_of_birth:
            user["date_of_birth"] = datetime.strptime(date_of_birth, "%Y-%m-%d").date()
        user = await crud_user.create(session=session, user=User(**user))
        await crud_wallet.create_wallet(session=session, user_id=user.id)
        await redis.delete(key)
        response.status_code = 200
        response.message = "Your account has been successfully verified. Please log in to continue."
    return response.build()

@router.post("/reset-password")
async def reset_password(email: str, session: AsyncSession = Depends(get_async_session)):
    with response_handler() as response:
        user = await crud_user.get_user_by_email(session=session, email=email)
        if user:
            code = randint(100000,999999)
            await redis.set(f"user:reset:password:{user.email}:{code}", value=dumps({"id":user.id}), ex=900)
            email_client.send_password_reset_email(recipient=user.email, fullname=user.fullname, code=code, template_name="emails/reset_password_user.html")

        response.status_code = 200
        response.message = "Please check your email. If your account exists, you will receive a verification code."
    return response.build()

@router.post("/reset-password/confirm")
async def reset_password_confirm(
    email: str = Form(...),
    code: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...), 
    session: AsyncSession = Depends(get_async_session)):
    with response_handler() as response:
        if new_password!=confirm_password:
            raise ValueError("Passwords do not match.")
        
        key = f"user:reset:password:{email}:{code}"
        user = await redis.get(key)
        if not user:
            raise ValueError("Invalid verification code or the code has expired.")
        user = loads(user)
        user = await crud_user.get_user_by_id(session=session, id=user.get("id"))
        user.password = Hasher.hash_password(new_password)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        await redis.delete(key)

        response.status_code = 200
        response.message = "Password has been reset successfully. Please log in using your new password."
    return response.build()