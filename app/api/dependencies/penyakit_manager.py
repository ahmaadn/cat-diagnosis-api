import logging
from typing import Any, Sequence

from fastapi import Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.sessions import get_async_session
from app.db.models.penyakit import Penyakit
from app.schemas.penyakit import PenyakitCreate, PenyakitUpdate
from app.utils.base_manager import BaseManager
from app.utils.common import ErrorCode
from app.utils.exceptions import AppExceptionError, DuplicateNamaError

logger = logging.getLogger(__name__)


class PenyakitManager(BaseManager[Penyakit, PenyakitCreate, PenyakitUpdate]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Penyakit)

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

    async def is_valid_id(self, item_id: str):
        exception = AppExceptionError(
            "ID tidak balid",
            f"ID: {item_id}",
            "Contoh Id Valid : P00001",
            error_code=self.error_codes["not_valid_id"],
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
        )

        if len(item_id) != 5:
            raise exception

        if item_id.isnumeric():
            raise exception

        code, num = item_id[:1], item_id[1:]
        if code != "P" or not num.isdigit():
            raise exception

        already_exist = await self.get_by_id(item_id)
        if already_exist:
            raise AppExceptionError(
                "ID di temukan sama",
                f"ID: {item_id}",
                status_code=status.HTTP_406_NOT_ACCEPTABLE,
                error_code=self.error_codes["duplicate_id"],
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

    async def create_id(self, penyakits: Sequence[Penyakit]) -> str:
        existing_ids = {penyakit.id for penyakit in penyakits}

        nums_ids = {int(penyakit.id[1:]) for penyakit in penyakits}
        expected = set(range(min(nums_ids), max(nums_ids) + 1))
        missing_nums = expected - nums_ids

        # Assign missing IDs
        for num in sorted(missing_nums):
            new_id = f"P{num:04d}"

            if new_id not in existing_ids:
                return new_id

        # Assign new IDs for remaining entries
        next_num = max(nums_ids, default=0) + 1
        while True:
            new_id = f"P{next_num:04d}"
            if new_id not in existing_ids:
                return new_id
            next_num += 1

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
