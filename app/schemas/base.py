from typing import TypeVar

from pydantic import BaseModel, ConfigDict

_T = TypeVar("_T")


class BaseSchema(BaseModel):
    """Base schema for all schemas."""

    model_config = ConfigDict(from_attributes=True)
