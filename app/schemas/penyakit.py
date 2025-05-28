from app.schemas.base import BaseSchema


class PenyakitCreate(BaseSchema):
    id_penyakit: str
    nama_penyakit: str


class PenyakitRead(BaseSchema):
    id_penyakit: str
    nama_penyakit: str
