from pydantic import Field

from app.schemas.base import BaseSchema
from app.schemas.mixin import IdMixinSchema, TimeStampMixinSchema


class GejalaCreate(BaseSchema):
    id: str | None = None
    nama: str
    pertanyaan: str
    deskripsi: str | None = None
    kelompoks: list[int] = Field(default_factory=list)


class GejalaUpdate(BaseSchema):
    nama: str | None = None
    deskripsi: str | None = None
    pertanyaan: str | None = None
    kelompoks: list[int] | None = None


class KelompokRead(BaseSchema):
    id: int
    nama: str


class GejalaRead(BaseSchema, TimeStampMixinSchema, IdMixinSchema):
    nama: str
    image_url: str | None = None
    deskripsi: str | None = None
    pertanyaan: str
    kelompoks: list[KelompokRead]


class SimpleGejalaRead(BaseSchema, IdMixinSchema):
    nama: str
    deskripsi: str | None = None
    pertanyaan: str
