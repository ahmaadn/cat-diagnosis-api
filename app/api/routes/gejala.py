from fastapi import APIRouter, Depends, status
from fastapi_utils.cbv import cbv
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.gejala_manager import GejalaManager, get_gejala_manager
from app.api.dependencies.sessions import get_async_session
from app.db.models.gejala import Gejala
from app.db.models.kelompok import Kelompok
from app.schemas.gejala import GejalaCreate, GejalaRead, GejalaUpdate
from app.schemas.kelompok import KelompokRead
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
    async def get_all_gejala(
        self, kelompok_id: int | None = None, page: int = 1, per_page: int = 200
    ):
        if kelompok_id:
            query = (
                select(Gejala)
                .join(Gejala.kelompoks)
                .filter(Kelompok.id == kelompok_id)
            )
        else:
            query = select(Gejala)
        return await paginate(self.session, query, page, per_page)

    @r.get("/gejala/{gejala_id}", response_model=GejalaRead)
    async def get_gejala_by_id(self, gejala_id: str):
        return await self.manager.get_by_id_or_fail(gejala_id)

    @r.put("/gejala/{gejala_id}", response_model=GejalaRead)
    async def update_gejala(self, gejala_id: str, new_data: GejalaUpdate):
        return await self.manager.update(item_id=gejala_id, item_update=new_data)

    @r.delete("/gejala/{gejala_id}", status_code=status.HTTP_202_ACCEPTED)
    async def delete_gejala(self, gejala_id: str):
        await self.manager.delete(item_id=gejala_id)
        return {"message": f"success delete gejala id {gejala_id}"}

    @r.get(
        "/gejala/{gejala_id}/kelompoks",
        response_model=PaginationSchema[KelompokRead],
        status_code=status.HTTP_200_OK,
    )
    async def get_detail_kelompoks_by_gejala(
        self, gejala_id: str, page: int = 1, per_page: int = 200
    ):
        query = (
            select(Kelompok).join(Kelompok.gejalas).filter(Gejala.id == gejala_id)
        )

        return await paginate(self.session, query, page, per_page)
