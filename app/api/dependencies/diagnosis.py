import logging
from collections import defaultdict
from typing import Optional, Sequence

from fastapi import APIRouter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.db.models.penyakit import Penyakit as PenyakitModel
from app.db.models.rule import Rule
from app.schemas.diagnosis import (
    DiagnosisRequest,
    DiagnosisResult,
    EvidenceDetail,
    PenyakitResult,
)
from app.schemas.penyakit import PenyakitRead

logger = logging.getLogger(__name__)
r = router = APIRouter(tags=["Diagnosis"])


class _PenyakitCalculationDetail(defaultdict):
    """
    Struktur data internal untuk mengakumulasi hasil perhitungan CF per penyakit.
    """

    cf_combined: float
    evidence: list[EvidenceDetail]
    penyakit_obj: Optional[PenyakitModel]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cf_combined = 0.0
        self.evidence = []
        self.penyakit_obj = None


class Diagnosis:
    @staticmethod
    def combine_cf(cf_old: float, cf_new: float) -> float:
        """
        Menggabungkan dua nilai Certainty Factor (CF) menggunakan formula standar.

        Formula ini menangani semua kombinasi nilai positif dan negatif CF.
        Nilai CF harus berada dalam rentang [-1, 1].

        Args:
            cf_old: Nilai CF yang sudah ada (akumulasi sebelumnya).
            cf_new: Nilai CF baru yang akan digabungkan (misalnya, CF dari aturan).

        Returns:
            Nilai CF gabungan.

        Raises:
            ValueError: Jika salah satu nilai CF berada di luar rentang [-1, 1].
        """
        if not (-1 <= cf_old <= 1 and -1 <= cf_new <= 1):
            raise ValueError("Nilai CF harus berada di antara -1 dan 1")

        if cf_old >= 0 and cf_new >= 0:  # Kedua CF positif
            return cf_old + cf_new * (1 - cf_old)
        if cf_old < 0 and cf_new < 0:  # Kedua CF negatif
            return cf_old + cf_new * (1 + cf_old)

        # Satu CF positif, satu negatif (konflik)
        denominator = 1 - min(abs(cf_old), abs(cf_new))
        if denominator == 0:
            # Terjadi jika CF = 1 dan CF = -1 (atau sebaliknya).
            # Keyakinan absolut yang berlawanan, menghasilkan ketidakpastian (0).
            return 0.0
        return (cf_old + cf_new) / denominator

    @staticmethod
    async def fetch_relevant_rules(
        session: AsyncSession, user_gejala_ids: set[str]
    ) -> Sequence[Rule]:
        """
        Mengambil semua aturan (Rule) yang relevan dengan gejala yang diberikan pengguna.

        Args:
            session: Sesi database SQLAlchemy AsyncSession.
            user_gejala_ids: set ID gejala yang dipilih oleh pengguna.

        Returns:
            Daftar objek Rule yang relevan, dengan relasi penyakit, gejala, dan rule_cfs
            sudah di-load (eager loading).
        """
        query = (
            select(Rule)
            .where(Rule.id_gejala.in_(user_gejala_ids))
            .options(
                joinedload(Rule.penyakit),
                joinedload(Rule.gejala),
                joinedload(Rule.rule_cfs),  # Untuk mengakses nilai CF dari pakar
            )
        )
        result = await session.execute(query)
        return result.scalars().unique().all()

    @staticmethod
    def calculate_diagnosis_cf(
        rules: list[Rule],
        user_cf_map: dict[str, float],
        pakar_id_filter: Optional[str] = None,
    ) -> dict[str, _PenyakitCalculationDetail]:
        """
        Menghitung Certainty Factor (CF) gabungan untuk setiap penyakit berdasarkan aturan
        dan CF pengguna.

        Args:
            rules: Daftar aturan (Rule) yang relevan.
            user_cf_map: Mapping dari ID gejala ke CF yang diberikan pengguna.
            pakar_id_filter: Jika disediakan, hanya CF dari pakar dengan ID ini yang
                            akan digunakan. Jika None, rata-rata CF dari semua pakar
                            pada aturan tersebut akan digunakan.

        Returns:
            Kamus yang memetakan ID penyakit ke detail perhitungan CF
            (_PenyakitCalculationDetail).
        """
        penyakit_accumulator: dict[str, _PenyakitCalculationDetail] = defaultdict(
            _PenyakitCalculationDetail
        )

        for rule in rules:
            if not rule.gejala:
                logger.warning(
                    f"Aturan {rule.id} tidak memiliki objek gejala terkait. Dilewati."
                )
                continue
            if not rule.penyakit or not rule.id_penyakit:
                logger.warning(
                    f"Aturan {rule.id} (gejala: {rule.id_gejala}) tidak memiliki penyakit "
                    f"terkait (id_penyakit: {rule.id_penyakit}). Dilewati."
                )
                continue

            penyakit_id: str = rule.id_penyakit  # type: ignore

            cf_pakar_value: Optional[float] = None
            if pakar_id_filter:  # Diagnosis berdasarkan pakar spesifik
                pakar_cf_obj = next(
                    (cf for cf in rule.rule_cfs if cf.id_pakar == pakar_id_filter), None
                )
                if pakar_cf_obj:
                    cf_pakar_value = pakar_cf_obj.nilai
            elif rule.rule_cfs:  # Memastikan ada CF dari pakar
                cf_pakar_value = sum(cf.nilai for cf in rule.rule_cfs) / len(rule.rule_cfs)

            if cf_pakar_value is None:
                logger.debug(
                    f"Tidak ada nilai CF pakar untuk aturan {rule.id} "
                    f"(gejala: {rule.id_gejala}) dengan filter pakar: {pakar_id_filter}. "
                    "Aturan ini dilewati untuk perhitungan."
                )
                continue

            cf_user = user_cf_map.get(rule.id_gejala, 0.0)
            cf_he = cf_pakar_value * cf_user  # CF hipotesis berdasarkan evidence

            current_data = penyakit_accumulator[penyakit_id]
            current_data.cf_combined = Diagnosis.combine_cf(current_data.cf_combined, cf_he)
            current_data.penyakit_obj = rule.penyakit

            evidence = EvidenceDetail(
                gejala=rule.gejala,  # type: ignore
                cf_user=cf_user,
                # Meskipun fieldnya cf_pakar_avg, ini akan berisi cf_pakar_value
                # yang bisa jadi nilai spesifik pakar atau rata-rata.
                cf_pakar_avg=round(cf_pakar_value, 4),
                cf_evidence=round(cf_he, 4),
            )
            current_data.evidence.append(evidence)

        return penyakit_accumulator

    @staticmethod
    def format_diagnosis_results(
        penyakit_data_map: dict[str, _PenyakitCalculationDetail],
    ) -> DiagnosisResult:
        """
        Memformat hasil perhitungan CF menjadi struktur DiagnosisResult.

        Args:
            penyakit_data_map: Kamus hasil dari _calculate_diagnosis_cf.

        Returns:
            Objek DiagnosisResult yang berisi daftar penyakit terurut berdasarkan skor
            keyakinan.
        """
        results: list[PenyakitResult] = []
        for penyakit_id, data in penyakit_data_map.items():
            if data.cf_combined > 0 and data.penyakit_obj:
                # Pastikan penyakit_obj adalah instance dari skema PenyakitRead jika
                # diperlukan Untuk sekarang, kita asumsikan struktur PenyakitModel
                # kompatibel atau akan dikonversi oleh FastAPI.
                penyakit_read_obj = PenyakitRead.model_validate(data.penyakit_obj)

                results.append(
                    PenyakitResult(
                        penyakit=penyakit_read_obj,  # type: ignore
                        certainty_score=round(data.cf_combined * 100, 2),
                        matching_gejala_count=len(data.evidence),
                        matching_gejala_ids=[ev.gejala.id for ev in data.evidence],
                        evidence_details=data.evidence,
                    )
                )
            elif data.cf_combined <= 0:
                penyakit_name = (
                    data.penyakit_obj.nama if data.penyakit_obj else f"ID {penyakit_id}"
                )
                logger.debug(
                    f"Penyakit '{penyakit_name}' memiliki CF gabungan <= 0 "
                    f"({data.cf_combined:.4f}), tidak dimasukkan dalam hasil."
                )
            elif not data.penyakit_obj:
                logger.warning(
                    f"Data penyakit untuk ID '{penyakit_id}' memiliki CF gabungan > 0 "
                    f"({data.cf_combined:.4f}) tetapi tidak ada objek penyakit terkait. "
                    "Tidak dimasukkan dalam hasil."
                )

        # Urutkan hasil berdasarkan certainty_score tertinggi
        ranked_results = sorted(results, key=lambda p: p.certainty_score, reverse=True)
        return DiagnosisResult(ranked_results=ranked_results)

    @staticmethod
    async def diagnosis(
        session: AsyncSession, request: DiagnosisRequest, pakar_id: str | None = None
    ):
        user_gejala_ids = {g.id_gejala for g in request.gejala_user}
        user_cf_map = {g.id_gejala: g.cf_user for g in request.gejala_user}

        if not user_gejala_ids:
            # Logger Only
            if pakar_id is None:
                logger.info("Tidak ada gejala yang diberikan untuk diagnosis.")
            else:
                logger.info(
                    "Tidak ada gejala yang diberikan untuk diagnosis oleh pakar "
                    f"{pakar_id}."
                )
            return DiagnosisResult(ranked_results=[])

        relevant_rules = await Diagnosis.fetch_relevant_rules(session, user_gejala_ids)
        if not relevant_rules:
            if pakar_id is None:
                logger.info(
                    "Tidak ada aturan yang relevan ditemukan untuk gejala yang diberikan."
                )
            else:
                logger.info(
                    "Tidak ada aturan relevan untuk gejala yang diberikan "
                    f"(pakar: {pakar_id})."
                )
            return DiagnosisResult(ranked_results=[])

        penyakit_cf_data = Diagnosis.calculate_diagnosis_cf(
            rules=list(relevant_rules), user_cf_map=user_cf_map, pakar_id_filter=pakar_id
        )

        diagnosis_result = Diagnosis.format_diagnosis_results(penyakit_cf_data)

        if pakar_id is None:
            logger.info(
                f"Diagnosis (rata-rata pakar) selesai. Ditemukan "
                f"{len(diagnosis_result.ranked_results)} penyakit potensial."
            )
        else:
            logger.info(
                f"Diagnosis oleh pakar {pakar_id} selesai. "
                f"Ditemukan {len(diagnosis_result.ranked_results)} penyakit potensial."
            )
        return diagnosis_result
