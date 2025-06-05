from app.schemas.base import BaseSchema


class PenyakitCreate(BaseSchema):
    id: str | None = None
    nama: str


class PenyakitUpdate(BaseSchema):
    nama: str


class PenyakitRead(BaseSchema):
    id: str
    nama: str
