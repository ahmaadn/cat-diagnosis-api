from fastapi import APIRouter, Depends, status
from fastapi_utils.cbv import cbv
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.kelompok_manager import (
    KelompokManager,
    get_kelompok_manager,
)
from app.api.dependencies.sessions import get_async_session
from app.schemas.base import ResponsePayload
from app.schemas.gejala import KelompokRead
from app.schemas.pagination import PaginationSchema

r = router = APIRouter(prefix="/kelompok", tags=["kelompok_gejala"])


@cbv(r)
class GejalaRoute:
    session: AsyncSession = Depends(get_async_session)
    manager: KelompokManager = Depends(get_kelompok_manager)

    @r.post(
        "/bulks",
        status_code=status.HTTP_201_CREATED,
        response_model=ResponsePayload[list[KelompokRead]],
    )
    async def bulks(self, data: list[str]):
        kelompoks = await self.manager.bulks(data)  # type: ignore
        return ResponsePayload(
            message=f"Kelompok Gekala Berhasil dibuat sebanyak {len(kelompoks)}",
            items=kelompoks,
        )

    @r.post(
        "/",
        status_code=status.HTTP_201_CREATED,
        response_model=ResponsePayload[KelompokRead],
    )
    async def add(self, data: str):
        kelompok = await self.manager.create(data)  # type: ignore
        return ResponsePayload(
            message="Kelompok Gekala Berhasil dibuat",
            items=kelompok,
        )

    @r.get(
        "/",
        status_code=status.HTTP_200_OK,
        response_model=PaginationSchema[KelompokRead],
    )
    async def get_all(self):
        data = await self.manager.fetch_all()

        return PaginationSchema(
            count=len(data), items=data, curr_page=1, total_page=1
        )
