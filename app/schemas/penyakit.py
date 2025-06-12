from pydantic import field_validator

from app.middleware.pagination import request_object
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
    image_url: str | None = None
    nama: str
    solusi: str
    deskripsi: str | None = None
    pencegahan: str | None = None

    @field_validator("image_url", mode="before")
    @classmethod
    def assemble_image_url(cls, v: str | None) -> str | None:
        """Prepend static image path if image_url is just a filename."""
        if (
            isinstance(v, str)
            and v
            and not v.startswith(("/static/image/", "http://", "https://"))
        ):
            return f"{request_object.get().base_url}static/image/{v}"
        return v
