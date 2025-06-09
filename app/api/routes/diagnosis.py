import logging
from collections import defaultdict
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.api.dependencies.sessions import get_async_session
from app.db.models.rule import Rule
from app.schemas.diagnosis import (
    DiagnosisRequest,
    DiagnosisResult,
    EvidenceDetail,
    PenyakitResult,
)

logger = logging.getLogger(__name__)
r = router = APIRouter(tags=["Diagnosis"])


def combine_cf(cf_old: float, cf_new: float) -> float:
    """
    Menggabungkan dua nilai Certainty Factor (CF) menggunakan formula standar.
    Formula ini menangani semua kombinasi nilai positif dan negatif.
    """
    # Pastikan nilai berada dalam rentang yang valid
    if not (-1 <= cf_old <= 1 and -1 <= cf_new <= 1):
        raise ValueError("Nilai CF harus berada di antara -1 dan 1")

    # Kasus 1: Kedua CF positif (meningkatkan keyakinan)
    if cf_old >= 0 and cf_new >= 0:
        return cf_old + cf_new * (1 - cf_old)

    # Kasus 2: Kedua CF negatif (meningkatkan ketidakyakinan)
    if cf_old < 0 and cf_new < 0:
        # Rumus asli: cf_old + cf_new * (1 + cf_old)
        # Ini sama dengan -(abs(cf_old) + abs(cf_new) * (1 - abs(cf_old)))
        return cf_old + cf_new * (1 + cf_old)

    # Kasus 3: Satu CF positif, satu negatif (konflik)
    denominator = 1 - min(abs(cf_old), abs(cf_new))
    if denominator == 0:
        # Ini terjadi jika CF = 1 dan CF = -1, keyakinan absolut yang berlawanan.
        # Dalam beberapa implementasi, ini menghasilkan 0.
        return 0.0

    return (cf_old + cf_new) / denominator


@r.post("/diagnosis", response_model=DiagnosisResult)
async def perform_diagnosis_v2(
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

    penyakit_cf: dict[Any, Any] = defaultdict(
        lambda: {"cf_combined": 0.0, "evidence": []}
    )

    for rule in relevant_rules:
        if not rule.rule_cfs:
            continue

        avg_cf_pakar = sum(cf.nilai for cf in rule.rule_cfs) / len(rule.rule_cfs)
        cf_user = user_cf_map.get(rule.id_gejala, 0.0)
        cf_he = avg_cf_pakar * cf_user

        penyakit_id = rule.id_penyakit
        current_cf = penyakit_cf[penyakit_id]["cf_combined"]
        penyakit_cf[penyakit_id]["cf_combined"] = combine_cf(current_cf, cf_he)  # type: ignore

        # Simpan objek penyakit
        penyakit_cf[penyakit_id]["penyakit_obj"] = rule.penyakit

        # --- KUMPULKAN DETAIL PERHITUNGAN ---
        evidence = EvidenceDetail(
            id_gejala=rule.gejala.id,
            cf_user=cf_user,
            cf_pakar_avg=round(avg_cf_pakar, 2),
            cf_evidence=round(cf_he, 4),
        )
        penyakit_cf[penyakit_id]["evidence"].append(evidence)  # type: ignore

    if not penyakit_cf:
        return DiagnosisResult(ranked_results=[])

    results = []
    for _, data in penyakit_cf.items():
        if data["cf_combined"] > 0:  # type: ignore
            results.append(
                PenyakitResult(
                    penyakit=data["penyakit_obj"],
                    certainty_score=round(data["cf_combined"] * 100, 2),
                    matching_gejala_count=len(data["evidence"]),
                    # Masukkan detail bukti ke dalam respons
                    evidence_details=data["evidence"],
                )
            )

    ranked_results = sorted(results, key=lambda p: p.certainty_score, reverse=True)
    return DiagnosisResult(ranked_results=ranked_results)
