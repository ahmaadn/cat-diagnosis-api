from pydantic import Field

from app.schemas.base import BaseSchema
from app.schemas.penyakit import PenyakitRead


class UserGejalaInput(BaseSchema):
    """Input gejala dari pengguna."""

    id_gejala: str = Field(..., description="ID Gejala yang dialami.")

    # Di sistem pakar CF, nilai keyakinan user juga penting.
    # Di sini kita hardcode 1.0 (sangat yakin), tapi bisa dibuat dinamis.
    cf_user: float = Field(
        1.0, description="Tingkat keyakinan user terhadap gejala ini.", ge=0, le=1
    )


class DiagnosisRequest(BaseSchema):
    """Request body untuk memulai diagnosis."""

    gejala_user: list[UserGejalaInput]


class PenyakitResult(BaseSchema):
    """Skema untuk satu hasil penyakit dalam diagnosis."""

    penyakit: PenyakitRead
    certainty_score: float = Field(
        ..., description="Skor akhir keyakinan dalam persentase (%)."
    )
    matching_gejala_count: int = Field(..., description="Jumlah gejala yang cocok.")


class DiagnosisResult(BaseSchema):
    """Skema untuk hasil akhir diagnosis yang sudah diurutkan."""

    ranked_results: list[PenyakitResult]
