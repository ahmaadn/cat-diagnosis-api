from app.schemas.base import BaseSchema


class PakarCreate(BaseSchema):
    id: str | None = None
    nama: str


class PakarRead(BaseSchema):
    id: str
    nama: str


class PakarUpdate(BaseSchema):
    nama: str
