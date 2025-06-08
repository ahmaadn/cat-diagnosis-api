from fastapi import APIRouter, Depends, status
from fastapi_utils.cbv import cbv
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.penyakit_manager import (
    PenyakitManager,
    get_penyakit_manager,
)
from app.api.dependencies.sessions import get_async_session
from app.db.models.penyakit import Penyakit
from app.schemas.pagination import PaginationSchema
from app.schemas.penyakit import PenyakitCreate, PenyakitRead, PenyakitUpdate
from app.utils.pagination import paginate

r = router = APIRouter(tags=["Penyakit"])


@cbv(router)
class _Penyakit:
    session: AsyncSession = Depends(get_async_session)
    manager: PenyakitManager = Depends(get_penyakit_manager)

    @r.post(
        "/penyakit",
        status_code=status.HTTP_201_CREATED,
        response_model=PenyakitRead,
    )
    async def create_penyakit(self, penyakit: PenyakitCreate):
        return await self.manager.create(penyakit)

    @r.get("/penyakit", response_model=PaginationSchema[PenyakitRead])
    async def get_all_penyakit(self, page=1, per_page=200):
        return await paginate(self.session, select(Penyakit), page, per_page)

    @r.get("/penyakit/{penyakit_id}", response_model=PenyakitRead)
    async def get_penyakit_by_id(self, penyakit_id: str):
        return await self.manager.get_by_id_or_fail(penyakit_id)

    @r.put("/penyakit/{penyakit_id}", response_model=PenyakitRead)
    async def update_pebyakit(self, penyakit_id: str, new_data: PenyakitUpdate):
        return await self.manager.update(item_id=penyakit_id, item_update=new_data)

    @r.delete("/penyakit/{penyakit_id}", response_model=PenyakitRead)
    async def delete_penyakit(self, penyakit_id: str):
        await self.manager.delete(item_id=penyakit_id)
        return {"message": f"success delete penyakit id {penyakit_id}"}

    # @r.get("/penyakit/{penyakit_id}/rules", response_model=PenyakitRead)
    # async def get_gejala_by_penyakit(self, penyakit_id: str, new_data: PenyakitUpdate):
    #     return await self.manager.update(item_id=penyakit_id, item_update=new_data)
