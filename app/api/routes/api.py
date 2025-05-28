from fastapi import APIRouter

from app.core.config import settings

from . import docs, pakar, penyakit

router = APIRouter(prefix=f"/api/{settings.API_V1_STR}")
router.include_router(docs.router)
router.include_router(pakar.router)
router.include_router(penyakit.router)


@router.get("/ping")
def ping():
    return "pong"
