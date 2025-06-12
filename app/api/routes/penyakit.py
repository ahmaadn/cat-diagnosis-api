from fastapi import APIRouter, Depends, status
from fastapi_utils.cbv import cbv
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.dependencies.penyakit_manager import (
    PenyakitManager,
    get_penyakit_manager,
)
from app.api.dependencies.sessions import get_async_session
from app.db.models.penyakit import Penyakit
from app.db.models.rule import Rule
from app.db.models.rule_cf import RuleCf
from app.schemas.pagination import PaginationSchema
from app.schemas.penyakit import PenyakitCreate, PenyakitRead, PenyakitUpdate
from app.schemas.rule import RuleByPenyakitRead
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
    async def get_all_penyakit(self, page: int = 1, per_page: int = 200):
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

    @r.get(
        "/penyakit/{penyakit_id}/rules",
        response_model=PaginationSchema[RuleByPenyakitRead],
        summary="Get Rules by Penyakit ID",
    )
    async def get_rules_by_penyakit(
        self, penyakit_id: str, page: int = 1, per_page: int = 20
    ):
        """
        Mengambil daftar semua aturan (rule) yang terkait dengan
        sebuah penyakit berdasarkan ID penyakit.
        """
        # 1. Pastikan penyakit dengan ID yang diberikan ada.
        # Manager akan throw 404 Not Found jika tidak ada.
        await self.manager.get_by_id_or_fail(penyakit_id)

        # 2. Buat query untuk mengambil rules
        query = (
            select(Rule)
            .where(Rule.id_penyakit == penyakit_id)
            .options(
                # Eager load relasi untuk menghindari query N+1
                selectinload(Rule.gejala),
                selectinload(Rule.penyakit),
                selectinload(Rule.rule_cfs).selectinload(RuleCf.pakar),
            )
        )

        # 3. Gunakan utility paginate untuk mendapatkan hasil
        return await paginate(self.session, query, page, per_page)
