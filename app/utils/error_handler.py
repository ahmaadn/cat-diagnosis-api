from fastapi import Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.utils.exceptions import AppExceptionError


async def global_exception_handler(_, ext: Exception):
    # print_exception(ext)  # masih digunakan ketika  ngedebug  # noqa: ERA001
    return JSONResponse(
        {
            "error": "Internal Server Error",
            "detail": ["An unexpected error occurred"],
        },
        500,
    )


async def app_exception_handler(_: Request, ext: AppExceptionError):
    """Handle application-specific exceptions."""
    return JSONResponse(
        status_code=ext.status_code or status.HTTP_404_NOT_FOUND,
        content=ext.dump(),
    )


async def validation_exception_handler(_: Request, exc: RequestValidationError):
    """Handle validation exceptions globally."""
    # Get the original 'detail' list of errors
    details = exc.errors()
    modified_details = []
    # Replace 'msg' with 'message' for each error
    for error in details:
        modified_details.append(
            {
                "loc": error["loc"],
                "messages": [error["msg"]],
                "error_code": error["type"].upper(),
            }
        )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder({"detail": modified_details}),
    )
