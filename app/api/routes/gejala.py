from fastapi import APIRouter, Depends
from fastapi_utils.cbv import cbv
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.sessions import get_async_session

r = router = APIRouter(prefix="/gejala")


@cbv(r)
class GejalaRoute:
    session: AsyncSession = Depends(get_async_session)
