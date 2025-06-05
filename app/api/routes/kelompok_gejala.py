from fastapi import APIRouter, Depends, status
from fastapi_utils.cbv import cbv
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.kelompok_manager import (
    KelompokManager,
    get_kelompok_manager,
)
from app.api.dependencies.sessions import get_async_session
from app.db.models.gejala import Kelompok
from app.schemas.gejala import (
    KelompokCreate,
    KelompokRead,
    KelompokUpdate,
)
from app.schemas.pagination import PaginationSchema
from app.utils.pagination import paginate

r = router = APIRouter(tags=["Kelompok"])


@cbv(router)
class _Kelompok:
    session: AsyncSession = Depends(get_async_session)
    manager: KelompokManager = Depends(get_kelompok_manager)

    @r.post(
        "/kelompok",
        status_code=status.HTTP_201_CREATED,
        response_model=KelompokRead,
    )
    async def create_kelompok(self, kelompok: KelompokCreate):
        return await self.manager.create(kelompok)

    @r.get("/kelompok", response_model=PaginationSchema[KelompokRead])
    async def get_all_kelompok(self):
        return await paginate(self.session, select(Kelompok), 1, 9999999)

    @r.get("/kelompok/{kelompok_id}", response_model=KelompokRead)
    async def get_kelompok_by_id(self, kelompok_id: int):
        return await self.manager.get_by_id_or_fail(kelompok_id)

    @r.put("/kelompok/{kelompok_id}", response_model=KelompokRead)
    async def update_kelompok(self, kelompok_id: int, new_data: KelompokUpdate):
        return await self.manager.update(item_id=kelompok_id, item_update=new_data)
