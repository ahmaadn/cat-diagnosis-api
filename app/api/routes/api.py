from fastapi import APIRouter

from app.core.config import settings

from . import (
    cf_term,
    dashboard,
    diagnosis,
    docs,
    gejala,
    kelompok,
    pakar,
    penyakit,
    rule,
)

router = APIRouter(prefix=f"/api/{settings.API_V1_STR}")
router.include_router(docs.router)
router.include_router(pakar.router)
router.include_router(penyakit.router)
router.include_router(gejala.router)
router.include_router(kelompok.router)
router.include_router(rule.router)
router.include_router(diagnosis.router)
router.include_router(cf_term.router)
router.include_router(dashboard.router)


@router.get("/ping")
def ping():
    return "pong"
