import logging
from typing import Any, Sequence

from fastapi import Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.base_manager import BaseManager
from app.api.dependencies.sessions import get_async_session
from app.db.models.pakar import Pakar
from app.schemas.pakar import PakarCreate, PakarUpdate
from app.utils.common import ErrorCode
from app.utils.exceptions import AppExceptionError, DuplicateNamaError

logger = logging.getLogger(__name__)


class PakarManager(BaseManager[Pakar, PakarCreate, PakarUpdate]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Pakar)

    async def validate_schema(self, item_in: PakarCreate):
        pakars = await self.get_all()

        if item_in.id is None:
            item_in.id = await self.create_id(pakars)

        await self.is_valid_id(item_in.id)
        await self.is_valid_nama(pakars, item_in.nama)

    @property
    def error_codes(self):
        return {
            "not_found": ErrorCode.PAKAR_NOT_FOUND,
            "duplicate_id": ErrorCode.ID_PAKAR_DUPLICATE,
            "duplicate_nama": ErrorCode.NAMA_PAKAR_DUPLICATE,
            "not_valid_id": ErrorCode.NOT_VALID_ID_PAKAR,
        }

    async def is_valid_id(self, data_id: str):
        exception = AppExceptionError(
            "ID tidak balid",
            f"ID: {data_id}",
            "Contoh Id Valid : PKR01",
            error_code=self.error_codes["not_valid_id"],
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
        )

        if len(data_id) != 5:
            raise exception

        if data_id.isnumeric():
            raise exception

        code, num = data_id[:3], data_id[3:]
        if code != "PKR" or not num.isdigit():
            raise exception

        already_exist = await self.get_by_id(data_id)
        if already_exist:
            raise AppExceptionError(
                "ID di temukan sama",
                f"ID: {data_id}",
                status_code=status.HTTP_406_NOT_ACCEPTABLE,
                error_code=self.error_codes["duplicate_id"],
            )

    async def create_id(self, pakars):
        existing_ids = {pakar.id for pakar in pakars}

        nums_ids = {int(pakar.id[3:]) for pakar in pakars}
        expected = set(range(min(nums_ids), max(nums_ids) + 1))
        missing_nums = expected - nums_ids

        # Assign missing IDs
        for num in sorted(missing_nums):
            new_id = f"PKR{num:02d}"

            if new_id not in existing_ids:
                return new_id

        # Assign new IDs for remaining entries
        next_num = max(nums_ids, default=0) + 1
        while True:
            new_id = f"PKR{next_num:02d}"
            if new_id not in existing_ids:
                return new_id
            next_num += 1

    async def is_valid_nama(self, pakars: Sequence[Pakar], nama: str):
        for pakar in pakars:
            if pakar.nama == nama:
                raise DuplicateNamaError(
                    "Nama di temukan sama",
                    f"Nama: {nama}",
                    status_code=status.HTTP_406_NOT_ACCEPTABLE,
                    error_code=self.error_codes["duplicate_nama"],
                )

    async def _validate_update(self, db_item: Pakar, update_data: dict[str, Any]):
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


async def get_pakar_manager(session: AsyncSession = Depends(get_async_session)):
    yield PakarManager(session)
