from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, UploadFile, File

from app.src.core.security import AuthService
from app.src.router.forum.crud import CRUDForum
from app.src.core.session import get_async_session
from app.src.utils.handler import response_handler
from app.src.utils.forum_utils import save_forum_image

router = APIRouter()
crud_forum = CRUDForum()
auth_service = AuthService()

@router.post("/")
async def create_post(
    caption: str | None = None,
    image: UploadFile = File(...),
    auth: dict = Depends(auth_service.require_access_token),
    session: AsyncSession = Depends(get_async_session)
):
    with response_handler() as response:
        url = await save_forum_image(image)
        post = await crud_forum.create_post(
            session=session,
            data={"user_id": auth["id"], "image_url": url, "caption": caption}
        )
        response.data = {"id": post.id, "image_url": post.image_url}
        response.message = "Post created"
        response.status_code = 201
    return response.build()

@router.post("/{post_id}/like")
async def like_post(
    post_id: str,
    session: AsyncSession = Depends(get_async_session),
    auth: dict = Depends(auth_service.require_access_token),
):
    with response_handler() as response:
        count = await crud_forum.toggle_like(session, post_id, auth["id"])
        response.data = {"like_count": count}
        response.message = "Updated"
        response.status_code = 200
    return response.build()

@router.post("/{post_id}/comment")
async def add_comment(
    post_id: str,
    comment: str,
    auth: dict = Depends(auth_service.require_access_token),
    session: AsyncSession = Depends(get_async_session)
):
    with response_handler() as response:
        c = await crud_forum.add_comment(
            session,
            {"post_id": post_id, "user_id": auth["id"], "comment": comment}
        )
        response.data = {"id": c.id, "comment": c.comment}
        response.message = "Comment added"
        response.status_code = 201
    return response.build()

@router.get("/")
async def get_posts(limit: int = 20, offset: int = 0, session: AsyncSession = Depends(get_async_session)):
    with response_handler() as response:
        posts = await crud_forum.list_posts(session, limit, offset)
        response.data = posts
        response.message = "OK"
    return response.build()

@router.get("/{post_id}")
async def get_post_detail(post_id: str, session: AsyncSession = Depends(get_async_session)):
    with response_handler() as response:
        post = await crud_forum.get_post(session, post_id)
        response.data = post
        response.message = "OK"
    return response.build()
