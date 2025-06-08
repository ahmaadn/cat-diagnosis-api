from app.schemas.base import BaseSchema
from app.schemas.mixin import IdIntegerMixinSchema, TimeStampMixinSchema


class KelomopokGejalaCreate(BaseSchema):
    id_gejala: str
    id_kelompok: int


class KelompokCreate(BaseSchema):
    nama: str
    deskripsi: str = ""


class KelompokRead(IdIntegerMixinSchema, TimeStampMixinSchema, BaseSchema):
    nama: str
    deskripsi: str


class KelompokUpdate(BaseSchema):
    nama: str | None = None
    deskripsi: str | None = None
