from pydantic import Field, model_validator

from app.schemas.base import BaseSchema
from app.schemas.gejala import GejalaRead
from app.schemas.pakar import PakarRead
from app.schemas.penyakit import PenyakitRead


# ==================================
class RuleCfCreate(BaseSchema):
    """Skema untuk menambahkan nilai CF dari pakar ke sebuah rule."""

    id_pakar: str = Field(..., description="ID Pakar yang memberikan nilai.")
    nilai: float = Field(
        ..., description="Nilai Certainty Factor (CF) dari pakar.", ge=0, le=1
    )


class RuleCfRead(BaseSchema):
    """Skema untuk membaca data RuleCF beserta relasinya."""

    pakar: PakarRead
    nilai: float


# ==================================
# Skema untuk Rule (Aturan)
# ==================================
class RuleCreate(BaseSchema):
    """Skema untuk membuat Rule baru."""

    id: str | None = None
    id_penyakit: str = Field(..., description="ID Penyakit yang menjadi kesimpulan.")
    id_gejala: str = Field(..., description="ID Gejala yang menjadi premis.")

    @model_validator(mode="after")
    def check_penyakit_and_gejala_not_same(self):
        # Ini hanya contoh validasi, bisa disesuaikan
        if self.id_penyakit == self.id_gejala:
            raise ValueError(
                "ID Penyakit dan Gejala tidak boleh sama dalam satu aturan."
            )
        return self


class RuleUpdate(BaseSchema):
    """Skema untuk memperbarui Rule."""

    id_penyakit: str | None = None
    id_gejala: str | None = None


class RuleRead(BaseSchema):
    """Skema untuk membaca data Rule beserta relasinya."""

    id: str
    penyakit: PenyakitRead
    gejala: GejalaRead
    rule_cfs: list[RuleCfRead] = Field(default_factory=list)
