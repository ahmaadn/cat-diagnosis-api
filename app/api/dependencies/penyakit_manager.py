import logging
from typing import Any, Sequence

from fastapi import Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.sessions import get_async_session
from app.db.models.penyakit import Penyakit
from app.schemas.penyakit import PenyakitCreate, PenyakitUpdate
from app.utils.base_manager import BaseManager
from app.utils.common import ErrorCode
from app.utils.exceptions import (
    DuplicateIDError,
    DuplicateNamaError,
    NotValidIDError,
)
from app.utils.id_healper import IDConfig

logger = logging.getLogger(__name__)


class PenyakitManager(BaseManager[Penyakit, PenyakitCreate, PenyakitUpdate]):
    def __init__(self, session: AsyncSession):
        super().__init__(
            session=session,
            model=Penyakit,
            id_config=IDConfig(
                prefix="P", length=5, numeric_length=4, example="P0001"
            ),
            field_id="id",
        )

    @property
    def error_codes(self):
        return {
            "not_found": ErrorCode.PENYAKIT_NOT_FOUND,
            "duplicate_id": ErrorCode.ID_PENYAKIT_DUPLICATE,
            "duplicate_nama": ErrorCode.NAMA_PENYAKIT_DUPLICATE,
            "not_valid_id": ErrorCode.NOT_VALID_ID_PENYAKIT,
        }

    async def validate_schema(self, item_in: PenyakitCreate):
        penyakits = await self.get_all()
        if item_in.id is None:
            item_in.id = await self.create_id(penyakits)

        await self.is_valid_id(item_in.id)
        await self.is_valid_nama(penyakits, item_in.nama)

    async def is_valid_id(self, data_id: str):
        is_valid, error_message = self.id_helper.validate_format(data_id)
        if not is_valid:
            raise NotValidIDError(
                error_message,
                f"Contoh ID valid: {self.id_config.example}",
                error_code=self.error_codes["not_valid_id"],
                status_code=status.HTTP_406_NOT_ACCEPTABLE,
            )

        # Check for existing ID
        already_exist = await self.get_by_id(data_id)
        if already_exist:
            raise DuplicateIDError(
                f"ID: {data_id} telah terdaftar",
                error_code=self.error_codes["duplicate_id"],
                status_code=status.HTTP_406_NOT_ACCEPTABLE,
            )

    async def is_valid_nama(self, penyakits: Sequence[Penyakit], nama: str):
        for penyakit in penyakits:
            if penyakit.nama == nama:
                raise DuplicateNamaError(
                    "Nama di temukan sama",
                    f"Nama: {nama}",
                    status_code=status.HTTP_406_NOT_ACCEPTABLE,
                    error_code=self.error_codes["duplicate_nama"],
                )

    async def create_id(self, existing_items: Sequence[Penyakit]) -> str:
        existing_ids, nums_ids = self.id_helper.extract_numeric_ids(existing_items)
        return self.id_helper.create_id(existing_ids, nums_ids)

    async def _validate_update(self, db_item: Penyakit, update_data: dict[str, Any]):
        validated_update_dict = {}
        pakars = await self.get_all()
        for field, value in update_data.items():
            if not hasattr(db_item, field):
                logger.warning(
                    f"Field '{field}' not found on {self._model_name} during update."
                )
                continue

            if field == "nama" and value != db_item.nama:
                await self.is_valid_nama(pakars, value)
                validated_update_dict[field] = value

        return validated_update_dict


async def get_penyakit_manager(session: AsyncSession = Depends(get_async_session)):
    yield PenyakitManager(session)
