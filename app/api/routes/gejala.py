from fastapi import APIRouter, Depends, status
from fastapi_utils.cbv import cbv
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.gejala_manager import GejalaManager, get_gejala_manager
from app.api.dependencies.sessions import get_async_session
from app.db.models.gejala import Gejala
from app.schemas.gejala import GejalaCreate, GejalaRead, GejalaUpdate
from app.schemas.pagination import PaginationSchema
from app.utils.pagination import paginate

r = router = APIRouter(tags=["Gejala"])


@cbv(router)
class _Pakar:
    session: AsyncSession = Depends(get_async_session)
    manager: GejalaManager = Depends(get_gejala_manager)

    @r.post(
        "/gejala",
        status_code=status.HTTP_201_CREATED,
        response_model=GejalaRead,
    )
    async def create_gejala(self, gejala: GejalaCreate):
        return await self.manager.create(gejala)

    @r.get("/gejala", response_model=PaginationSchema[GejalaRead])
    async def get_all_gejala(self):
        return await paginate(self.session, select(Gejala), 1, 9999999)

    @r.get("/gejala/{gejala_id}", response_model=GejalaRead)
    async def get_gejala_by_id(self, gejala_id: str):
        return await self.manager.get_by_id_or_fail(gejala_id)

    @r.put("/gejala/{gejala_id}", response_model=GejalaRead)
    async def update_gejala(self, gejala_id: str, new_data: GejalaUpdate):
        return await self.manager.update(item_id=gejala_id, item_update=new_data)
