from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.base_manager import BaseManager
from app.api.dependencies.sessions import get_async_session
from app.db.models.penyakit import Penyakit
from app.schemas.penyakit import PenyakitCreate
from app.utils.common import ErrorCode


class PenyakitManager(BaseManager):
    def __init__(self, session: AsyncSession):
        super().__init__(session, "P", 5)

    @property
    def model_class(self):
        return Penyakit

    @property
    def create_schema_class(self):
        return PenyakitCreate

    @property
    def id_field_name(self):
        return "id_penyakit"

    @property
    def name_field_name(self):
        return "nama_penyakit"

    @property
    def error_codes(self):
        return {
            "duplicate_id": ErrorCode.DUPLICATE_ID_PENYAKIT,
            "duplicate_name": ErrorCode.DUPLICATE_NAMA_PENYAKIT,
            "not_valid_id": ErrorCode.NOT_VALID_ID_PENYAKIT,
        }


def get_penyakit_manager(session: AsyncSession = Depends(get_async_session)):
    """
    Dependency function that provides an instance of PenyakitManager
    using the given database session.
    """
    yield PenyakitManager(session)
