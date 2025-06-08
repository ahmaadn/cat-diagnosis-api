import uuid
from datetime import datetime

from pydantic import BaseModel


class IdMixinSchema(BaseModel):
    id: str


class IdIntegerMixinSchema(BaseModel):
    id: int


class UUIDMixinSchema(BaseModel):
    id: uuid.UUID


class TimeStampMixinSchema(BaseModel):
    create_at: datetime
    update_at: datetime
