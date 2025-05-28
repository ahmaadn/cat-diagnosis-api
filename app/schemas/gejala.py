from app.schemas.base import BaseSchema


class GejalaCreate(BaseSchema):
    id_gejala: str
    nama_gejala: str
    kategori: str | None = None
