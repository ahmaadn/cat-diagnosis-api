from starlette.middleware import Middleware

from .pagination import PaginationMiddleware

__all__ = ("PaginationMiddleware", "middleware")

middleware = [Middleware(PaginationMiddleware)]
