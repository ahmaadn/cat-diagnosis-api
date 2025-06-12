from pydantic import Field

from app.schemas.base import BaseSchema
from app.schemas.gejala import SimpleGejalaRead
from app.schemas.penyakit import PenyakitRead


class UserGejalaInput(BaseSchema):
    """Input gejala dari pengguna."""

    id_gejala: str = Field(..., description="ID Gejala yang dialami.")

    # Di sistem pakar CF, nilai keyakinan user juga penting.
    # Di sini kita hardcode 1.0 (sangat yakin), tapi bisa dibuat dinamis.
    cf_user: float = Field(
        1.0, description="Tingkat keyakinan user terhadap gejala ini.", ge=-1, le=1
    )


class EvidenceDetail(BaseSchema):
    """
    Skema untuk merinci perhitungan setiap bukti (gejala) yang cocok.
    """

    gejala: SimpleGejalaRead = Field(..., description="ID Gejala yang cocok.")
    cf_user: float = Field(
        ..., description="Nilai keyakinan yang dimasukkan pengguna untuk gejala ini."
    )
    cf_pakar_avg: float = Field(
        ..., description="Rata-rata nilai CF dari semua pakar untuk aturan ini."
    )
    cf_evidence: float = Field(
        ..., description="Hasil perkalian CF Pakar dengan CF Pengguna (CF H,E)."
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
    matching_gejala_ids: list[str] = Field(
        default_factory=list, description="ID gejala yang cocok."
    )
    evidence_details: list[EvidenceDetail] = Field(
        default_factory=list,
        description="Rincian perhitungan untuk setiap gejala yang cocok.",
    )


class DiagnosisResult(BaseSchema):
    """Skema untuk hasil akhir diagnosis yang sudah diurutkan."""

    ranked_results: list[PenyakitResult]
