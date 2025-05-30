from fastapi import APIRouter, Depends
from fastapi_utils.cbv import cbv
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.sessions import get_async_session

r = router = APIRouter(tags=["Gejala"])


@cbv(r)
class _Gejala:
    session: AsyncSession = Depends(get_async_session)
