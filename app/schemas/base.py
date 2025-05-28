from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

_T = TypeVar("_T")


class BaseSchema(BaseModel):
    """Base schema for all schemas."""

    model_config = ConfigDict(from_attributes=True)


class ResponsePayload(BaseSchema, Generic[_T]):
    message: str
    items: _T
