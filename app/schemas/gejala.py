from app.schemas.base import BaseSchema


class KelompokCreate(BaseSchema):
    nama: str


class KelompokRead(BaseSchema):
    id: int
    nama: str


class KelompokUpdate(BaseSchema):
    nama: str


class GejalaCreate(BaseSchema):
    id: str | None = None
    nama: str
    id_kelompok: list[int]


class GejalaUpdate(BaseSchema):
    nama: str | None = None
    id_kelompok: list[int] | None = None


class KelomopokGejalaCreate(BaseSchema):
    id_gejala: str
    id_kelompok: int


class GejalaRead(BaseSchema):
    id: str
    nama: str
    kelompoks: list[KelompokRead]
