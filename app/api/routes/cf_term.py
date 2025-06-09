from fastapi import APIRouter
from pydantic import Field

from app.schemas.base import BaseSchema

r = router = APIRouter(tags=["Certainty Factor Terms"])


class CfTermRead(BaseSchema):
    """Skema untuk menampilkan istilah CF dan nilainya."""

    term: str = Field(..., description="Istilah linguistik untuk tingkat keyakinan.")
    value: float = Field(
        ..., description="Nilai numerik CF yang sesuai (-1 hingga 1)."
    )


CF_TERMS_DATA = [
    {"term": "Pasti Ya", "value": 1.0},
    {"term": "Kemungkinan Besar Ya", "value": 0.75},
    {"term": "Bisa Jadi Ya", "value": 0.50},
    {"term": "Kemungkinan Kecil Ya", "value": 0.25},
    {"term": "Tidak Tahu / Tidak Yakin", "value": 0.0},
    {"term": "Kemungkinan Kecil Tidak", "value": -0.25},
    {"term": "Bisa Jadi Tidak", "value": -0.50},
    {"term": "Kemungkinan Besar Tidak", "value": -0.75},
    {"term": "Tidak", "value": -1.0},
]


@r.get(
    "/cf-terms",
    response_model=list[CfTermRead],
    summary="Dapatkan Daftar Istilah CF",
)
async def get_cf_terms():
    """
    Mengembalikan daftar istilah tingkat keyakinan (Certainty Terms)
    yang bisa dipilih oleh pengguna saat melakukan diagnosis.
    """
    return CF_TERMS_DATA
