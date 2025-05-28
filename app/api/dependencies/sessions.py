from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import async_session_maker


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Get an async session.
    This function is used to create a new async session for each request.
    """
    async with async_session_maker() as session:
        yield session
