from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.src.models.forum import ForumPost, ForumLike, ForumComment

class CRUDForum:
    async def create_post(self, session: AsyncSession, data: dict):
        post = ForumPost(**data)
        session.add(post)
        await session.commit()
        await session.refresh(post)
        return post

    async def get_post(self, session: AsyncSession, post_id: str):
        result = await session.execute(
            select(ForumPost).where(ForumPost.id == post_id)
        )
        return result.scalar_one_or_none()

    async def list_posts(self, session: AsyncSession, limit=20, offset=0):
        result = await session.execute(
            select(ForumPost)
            .order_by(ForumPost.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()

    async def toggle_like(self, session: AsyncSession, post_id: str, user_id: str):
        post = await self.get_post(session, post_id)
        if not post:
            raise FileNotFoundError("Post not found.")
        
        result = await session.execute(
            select(ForumLike).where(
                ForumLike.post_id == post_id,
                ForumLike.user_id == user_id
            )
        )
        existing = result.scalar_one_or_none()

        if not existing:
            new_like = ForumLike(post_id=post_id, user_id=user_id)
            session.add(new_like)
            post.like_count += 1

        else:
            await session.delete(existing)
            post.like_count -= 1

        await session.commit()
        return post.like_count

    async def add_comment(self, session: AsyncSession, data: dict):
        comment = ForumComment(**data)
        session.add(comment)

        post = await self.get_post(session, data["post_id"])
        post.comment_count += 1

        await session.commit()
        await session.refresh(comment)
        return comment
