from app.schemas.base import BaseSchema
from app.schemas.mixin import IdMixinSchema, TimeStampMixinSchema


class PenyakitCreate(BaseSchema):
    id: str | None = None
    nama: str
    solusi: str
    deskripsi: str | None = None
    pencegahan: str | None = None


class PenyakitUpdate(BaseSchema):
    nama: str | None = None
    solusi: str | None = None
    deskripsi: str | None = None
    pencegahan: str | None = None


class PenyakitRead(BaseSchema, TimeStampMixinSchema, IdMixinSchema):
    nama: str
    solusi: str
    deskripsi: str
    pencegahan: str
