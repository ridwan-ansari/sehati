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
    authentication: dict = Depends(auth_service.require_access_token),
    session: AsyncSession = Depends(get_async_session)
):
    with response_handler() as response:
        url = await save_forum_image(image)
        post = await crud_forum.create_post(
            session=session,
            data={"user_id": authentication["id"], "image_url": url, "caption": caption}
        )
        response.data = {"id": post.id, "image_url": post.image_url}
        response.message = "Post created"
        response.status_code = 201
    return response.build()

@router.post("/{post_id}/like")
async def like_post(
    post_id: str,
    session: AsyncSession = Depends(get_async_session),
    authentication: dict = Depends(auth_service.require_access_token),
):
    with response_handler() as response:
        response.data = await crud_forum.toggle_like(session, post_id, authentication["id"])
        response.message = "Updated"
        response.status_code = 200
    return response.build()

@router.post("/{post_id}/comment")
async def add_comment(
    post_id: str,
    comment: str,
    session: AsyncSession = Depends(get_async_session),
    authentication: dict = Depends(auth_service.require_access_token),
):
    with response_handler() as response:
        c = await crud_forum.add_comment(
            session,
            {"post_id": post_id, "user_id": authentication["id"], "comment": comment}
        )
        response.data = {"id": c.id, "comment": c.comment}
        response.message = "Comment added"
        response.status_code = 201
    return response.build()

@router.get("/")
async def get_posts(
    limit: int = 20, 
    offset: int = 0, 
    session: AsyncSession = Depends(get_async_session),
    authentication: dict = Depends(auth_service.require_access_token)
):
    with response_handler() as response:
        posts = await crud_forum.list_posts(session, limit, offset)

        post_ids = [p.id for p in posts]
        liked_posts = await crud_forum.get_user_liked_posts(session, authentication["id"], post_ids)
        response.data = [
            {
                "id": post.id,
                "like_count": post.like_count,
                "created_at": post.created_at,
                "image_url": post.image_url,
                "caption": post.caption,
                "is_liked": post.id in liked_posts,
                "comment_count": post.comment_count,
                "user": {
                    "id": post.user.id,
                    "nickname": post.user.nickname,
                    "avatar": post.user.picture
                }
            } for post in posts]
        response.message = "OK"
    return response.build()

@router.get("/{post_id}")
async def get_post_detail(
    post_id: str, 
    session: AsyncSession = Depends(get_async_session),
    authentication: dict = Depends(auth_service.require_access_token),
):
    with response_handler() as response:
        post = await crud_forum.get_post(session, post_id)
        liked = await crud_forum.user_liked(session, post_id, authentication["id"])

        data = {
            "id": post.id,
            "caption": post.caption,
            "image_url": post.image_url,
            "like_count": post.like_count,
            "comment_count": post.comment_count,
            "is_liked": liked,
            "created_at": post.created_at,
            "user": {
                "id": post.user.id,
                "nickname": post.user.nickname,
                "avatar": post.user.picture
            },
            "comments": [
                {
                    "comment": c.comment,
                    "created_at": c.created_at,
                    "user": {
                        "id": c.user.id,
                        "nickname": c.user.nickname,
                        "avatar": c.user.picture
                    }
                }
                for c in post.comments
            ]
        }
        response.data = data
        response.message = "OK"
    return response.build()
