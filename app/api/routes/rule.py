from fastapi import APIRouter, Depends, status
from fastapi_utils.cbv import cbv
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.dependencies.rule_manager import RuleManager, get_rule_manager
from app.api.dependencies.sessions import get_async_session
from app.db.models.rule import Rule
from app.db.models.rule_cf import RuleCf
from app.schemas.pagination import PaginationSchema
from app.schemas.rule import RuleCfCreate, RuleCreate, RuleRead
from app.utils.pagination import paginate

r = router = APIRouter(tags=["Rule (Basis Aturan)"])


@cbv(router)
class _Rule:
    session: AsyncSession = Depends(get_async_session)
    manager: RuleManager = Depends(get_rule_manager)

    @r.post("/rules", status_code=status.HTTP_201_CREATED, response_model=RuleRead)
    async def create_rule(self, rule: RuleCreate):
        """Membuat aturan baru antara Gejala dan Penyakit."""
        return await self.manager.create(rule)

    @r.get("/rules", response_model=PaginationSchema[RuleRead])
    async def get_all_rules(self, page: int = 1, per_page: int = 20):
        """Mendapatkan semua aturan dengan paginasi."""
        query = select(Rule).options(
            selectinload(Rule.penyakit),
            selectinload(Rule.gejala),
            selectinload(Rule.rule_cfs).selectinload(RuleCf.pakar),
        )
        return await paginate(self.session, query, page, per_page)

    @r.get("/rules/{rule_id}", response_model=RuleRead)
    async def get_rule_by_id(self, rule_id: str):
        """Mendapatkan detail satu aturan."""
        return await self.manager.get_by_id_or_fail(rule_id)

    @r.delete("/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
    async def delete_rule(self, rule_id: str):
        """Menghapus sebuah aturan."""
        await self.manager.delete(item_id=rule_id)

    @r.post("/rules/{rule_id}/cf", response_model=RuleRead)
    async def add_rule_cf(self, rule_id: str, cf_data: RuleCfCreate):
        """Menambahkan atau memperbarui nilai CF dari pakar untuk sebuah aturan."""
        await self.manager.add_or_update_cf(rule_id, cf_data)
        return await self.manager.get_by_id_or_fail(rule_id)
