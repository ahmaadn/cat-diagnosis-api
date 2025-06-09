from fastapi import APIRouter
from pydantic import Field

from app.schemas.base import BaseSchema

r = router = APIRouter(tags=["Dashboard"])


class SystemStats(BaseSchema):
    """Skema untuk menampilkan statistik sistem secara keseluruhan."""

    total_penyakit: int = Field(
        ..., description="Jumlah total penyakit yang terdaftar dalam sistem."
    )
    total_gejala: int = Field(
        ..., description="Jumlah total gejala yang terdaftar dalam sistem."
    )
    total_pakar: int = Field(
        ..., description="Jumlah total pakar yang terdaftar dalam sistem."
    )
    total_kelompok_gejala: int = Field(
        ..., description="Jumlah total kelompok gejala yang terdaftar dalam sistem."
    )
    total_rules: int = Field(
        ..., description="Jumlah total aturan (rules) yang terdaftar dalam sistem."
    )


class CfTermRead(BaseSchema):
    """Skema untuk menampilkan istilah CF dan nilainya."""

    term: str = Field(..., description="Istilah linguistik untuk tingkat keyakinan.")
    value: float = Field(
        ..., description="Nilai numerik CF yang sesuai (-1 hingga 1)."
    )
