from typing import Any

from fastapi import status

from .common import ErrorCode


class AppExceptionError(Exception):
    error_code: ErrorCode | str | None = ErrorCode.APP_ERROR

    def __init__(
        self,
        *messages: str,
        error_code: ErrorCode | None = None,
        status: int = status.HTTP_404_NOT_FOUND,
        **kwargs,
    ):
        if error_code is not None:
            self.error_code = error_code

        self.messages = list(messages)
        self.status_code = status
        self.kwargs = kwargs or {}

        super().__init__(self.messages)

    def __str__(self):
        return (
            f"[{self.error_code}] {' | '.join(self.messages)}"
            if self.messages
            else f"[{self.error_code}]"
        )

    def dump(self) -> dict[str, Any]:
        return {
            "error_code": str(self.error_code),
            "messages": self.messages,
            **self.kwargs,
        }


class DuplicateIDError(AppExceptionError): ...


class DuplicateNamaError(AppExceptionError): ...


class NotValidIDError(AppExceptionError): ...
