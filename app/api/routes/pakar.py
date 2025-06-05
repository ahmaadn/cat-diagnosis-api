from fastapi import APIRouter, Depends, status
from fastapi_utils.cbv import cbv
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.pakar_manager import PakarManager, get_pakar_manager
from app.api.dependencies.sessions import get_async_session
from app.db.models.pakar import Pakar
from app.schemas.pagination import PaginationSchema
from app.schemas.pakar import PakarCreate, PakarRead, PakarUpdate
from app.utils.pagination import paginate

r = router = APIRouter(tags=["Pakar"])


@cbv(router)
class _Pakar:
    session: AsyncSession = Depends(get_async_session)
    manager: PakarManager = Depends(get_pakar_manager)

    @r.post(
        "/pakar",
        status_code=status.HTTP_201_CREATED,
        response_model=PakarRead,
    )
    async def create_pakar(self, pakar: PakarCreate):
        return await self.manager.create(pakar)

    @r.get("/pakar", response_model=PaginationSchema[PakarRead])
    async def get_all_pakar(self):
        return await paginate(self.session, select(Pakar), 1, 9999999)

    @r.get("/pakar/{pakar_id}", response_model=PakarRead)
    async def get_pakar_by_id(self, pakar_id: str):
        return await self.manager.get_by_id_or_fail(pakar_id)

    @r.put("/pakar/{pakar_id}", response_model=PakarRead)
    async def update_pakar(self, pakar_id: str, new_data: PakarUpdate):
        return await self.manager.update(item_id=pakar_id, item_update=new_data)
