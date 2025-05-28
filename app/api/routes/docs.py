from fastapi import APIRouter
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse

from app.core.config import settings

r = router = APIRouter(prefix="/docs")


@router.get("", include_in_schema=False)
async def docs() -> HTMLResponse:
    return get_swagger_ui_html(
        openapi_url=f"/api/{settings.API_V1_STR}/openapi.json",
        title=f"{settings.PROJECT_NAME} | Docs Api {settings.API_V1_STR}",
        swagger_favicon_url="/static/favicon.ico",
        oauth2_redirect_url="/",
    )
