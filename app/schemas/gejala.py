from app.schemas.base import BaseSchema


class GejalaCreate(BaseSchema):
    id_gejala: str | None = None
    nama_gejala: str
    kategori: int


class KelompokCreate(BaseSchema):
    nama_kelompok: str


class KelompokRead(BaseSchema):
    id_kelompok: int
    nama_kelompok: str
