from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.diagnosis import Diagnosis, logger
from app.api.dependencies.pakar_manager import PakarManager, get_pakar_manager
from app.api.dependencies.sessions import get_async_session
from app.schemas.diagnosis import (
    DiagnosisRequest,
    DiagnosisResult,
)

r = router = APIRouter(tags=["Diagnosis"])


@r.post(
    "/diagnosis",
    response_model=DiagnosisResult,
    summary="Lakukan Diagnosis (Rata-rata Pakar)",
)
async def perform_diagnosis_v2(
    request: DiagnosisRequest,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Melakukan diagnosis penyakit berdasarkan gejala yang diberikan pengguna.
    """
    logger.info(
        f"Memulai diagnosis (rata-rata pakar) untuk {len(request.gejala_user)} gejala."
    )
    return await Diagnosis.diagnosis(session, request, pakar_id=None)


@r.post(
    "/diagnosis/{pakar_id}",
    response_model=DiagnosisResult,
    summary="Lakukan Diagnosis (Pakar Spesifik)",
)
async def perform_diagnosis_by_pakar(
    pakar_id: str,
    request: DiagnosisRequest,
    session: AsyncSession = Depends(get_async_session),
    pakar_manager: PakarManager = Depends(get_pakar_manager),
):
    """
    Melakukan diagnosis penyakit berdasarkan gejala dari pengguna, menggunakan
    nilai Certainty Factor (CF) dari **satu pakar spesifik**.
    """
    logger.info(
        f"Memulai diagnosis oleh pakar spesifik ID: {pakar_id} untuk "
        f"{len(request.gejala_user)} gejala."
    )
    # Validasi pakar
    await pakar_manager.get_by_id_or_fail(pakar_id)
    return await Diagnosis.diagnosis(session, request, pakar_id=pakar_id)
