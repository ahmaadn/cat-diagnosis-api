from fastapi import APIRouter, Depends, status
from fastapi_utils.cbv import cbv
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.penyakit_manager import (
    PenyakitManager,
)
from app.api.dependencies.sessions import get_async_session
from app.db.models.penyakit import Penyakit
from app.schemas.base import ResponsePayload
from app.schemas.pagination import PaginationSchema
from app.schemas.penyakit import PenyakitCreate, PenyakitRead
from app.utils.pagination import paginate

router = APIRouter(prefix="/penyakit", tags=["Penyakit"])


@cbv(router)
class PenyakitRoute:
    session: AsyncSession = Depends(get_async_session)

    def __init__(self):
        self.manager = PenyakitManager(self.session)

    @router.post(
        "/bulks",
        status_code=status.HTTP_201_CREATED,
        response_model=ResponsePayload[list[PenyakitRead]],
    )
    async def add_penyakit_bulks(self, data: list[str | PenyakitCreate]):
        penyakits = await self.manager.bulks(data)
        return ResponsePayload(message="Berhasil membuat penyakit", items=penyakits)

    @router.get(
        "/",
        status_code=status.HTTP_200_OK,
        response_model=PaginationSchema[PenyakitRead],
    )
    async def get_all_penyakits(self):
        return await paginate(self.session, select(Penyakit), page=1, per_page=9999)
