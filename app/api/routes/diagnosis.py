import logging
from collections import defaultdict

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.api.dependencies.sessions import get_async_session
from app.db.models.rule import Rule
from app.schemas.diagnosis import DiagnosisRequest, DiagnosisResult, PenyakitResult

logger = logging.getLogger(__name__)
r = router = APIRouter(tags=["Diagnosis"])


def combine_cf(cf1: float, cf2: float) -> float:
    """Menggabungkan dua nilai Certainty Factor."""
    if cf1 >= 0 and cf2 >= 0:
        return cf1 + cf2 * (1 - cf1)
    if cf1 < 0 and cf2 < 0:
        return cf1 + cf2 * (1 + cf1)
    return (cf1 + cf2) / (1 - min(abs(cf1), abs(cf2)))


@r.post("/diagnosis", response_model=DiagnosisResult)
async def perform_diagnosis(
    request: DiagnosisRequest,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Endpoint utama untuk melakukan diagnosis berdasarkan gejala dari pengguna.
    """
    user_gejala_ids = {g.id_gejala for g in request.gejala_user}
    user_cf_map = {g.id_gejala: g.cf_user for g in request.gejala_user}

    # 1. Ambil semua rule yang relevan dengan gejala yang diberikan
    relevant_rules_query = (
        select(Rule)
        .where(Rule.id_gejala.in_(user_gejala_ids))
        .options(joinedload(Rule.penyakit), joinedload(Rule.rule_cfs))
    )
    result = await session.execute(relevant_rules_query)
    relevant_rules = result.scalars().unique().all()

    # 2. Kelompokkan rule berdasarkan penyakit dan hitung CF gabungan
    penyakit_cf = defaultdict(lambda: {"cf_combined": 0.0, "matching_gejala": set()})

    for rule in relevant_rules:
        if not rule.rule_cfs:
            continue

        # Ambil rata-rata nilai CF dari semua pakar untuk rule ini
        avg_cf_pakar = sum(cf.nilai for cf in rule.rule_cfs) / len(rule.rule_cfs)

        # Dapatkan CF dari user untuk gejala ini
        cf_user = user_cf_map.get(rule.id_gejala, 0.0)

        # Hitung CF evidence (CF H,E)
        cf_he = avg_cf_pakar * cf_user

        # Gabungkan CF evidence dengan CF yang sudah ada untuk penyakit ini
        current_cf = penyakit_cf[rule.id_penyakit]["cf_combined"]
        penyakit_cf[rule.id_penyakit]["cf_combined"] = combine_cf(current_cf, cf_he)  # type: ignore
        penyakit_cf[rule.id_penyakit]["matching_gejala"].add(rule.id_gejala)  # type: ignore
        # Simpan objek penyakit untuk nanti
        penyakit_cf[rule.id_penyakit]["penyakit_obj"] = rule.penyakit

    if not penyakit_cf:
        return DiagnosisResult(ranked_results=[])

    # 3. Bentuk hasil akhir
    results = []
    for _, data in penyakit_cf.items():
        results.append(
            PenyakitResult(
                penyakit=data["penyakit_obj"],  # type: ignore
                certainty_score=round(
                    data["cf_combined"] * 100,  # type: ignore
                    2,
                ),  # Ubah ke persentase
                matching_gejala_count=len(data["matching_gejala"]),  # type: ignore
            )
        )

    # 4. Urutkan hasil dari skor tertinggi ke terendah
    ranked_results = sorted(results, key=lambda p: p.certainty_score, reverse=True)

    return DiagnosisResult(ranked_results=ranked_results)
