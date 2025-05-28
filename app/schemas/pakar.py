from app.schemas.base import BaseSchema


class PakarCreate(BaseSchema):
    nama_pakar: str


class PakarRead(BaseSchema):
    id_pakar: int
    nama_pakar: str


class PakarEdit(BaseSchema):
    nama_pakar: str
