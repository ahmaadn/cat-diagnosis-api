from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.sessions import get_async_session
from app.db.models.gejala import Gejala
from app.db.models.kelompok import Kelompok
from app.db.models.pakar import Pakar
from app.db.models.penyakit import Penyakit
from app.db.models.rule import Rule
from app.schemas.other import SystemStats

r = router = APIRouter(tags=["Dashboard"])


@r.get(
    "/dashboard/statistics",
    response_model=SystemStats,
    summary="Dapatkan Statistik Sistem",
)
async def get_system_statistics(session: AsyncSession = Depends(get_async_session)):
    """
    Mengembalikan data statistik dasar dari sistem pakar,
    seperti jumlah penyakit, gejala, pakar, dan aturan.
    """
    total_penyakit = (
        await session.execute(select(func.count(Penyakit.id)))
    ).scalar_one()
    total_gejala = (
        await session.execute(select(func.count(Gejala.id)))
    ).scalar_one()
    total_pakar = (await session.execute(select(func.count(Pakar.id)))).scalar_one()
    total_kelompok = (
        await session.execute(select(func.count(Kelompok.id)))
    ).scalar_one()
    total_rules = (await session.execute(select(func.count(Rule.id)))).scalar_one()

    return SystemStats(
        total_penyakit=total_penyakit,
        total_gejala=total_gejala,
        total_pakar=total_pakar,
        total_kelompok_gejala=total_kelompok,
        total_rules=total_rules,
    )
