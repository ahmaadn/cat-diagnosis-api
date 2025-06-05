import logging
from typing import Sequence

from fastapi import Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.base_manager import BaseManager
from app.api.dependencies.kelompok_manager import (
    KelompokGejalaManager,
    KelompokManager,
)
from app.api.dependencies.sessions import get_async_session
from app.db.models.gejala import Gejala
from app.schemas.gejala import GejalaCreate, GejalaUpdate
from app.utils.common import ErrorCode
from app.utils.exceptions import AppExceptionError, DuplicateNamaError

logger = logging.getLogger(__name__)


class GejalaManager(BaseManager[Gejala, GejalaCreate, GejalaUpdate]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Gejala)
        self.kelompok_manager = KelompokManager(session)
        self.kelompok_gejala_manager = KelompokGejalaManager(session)

    @property
    def error_codes(self):
        return {
            "not_found": ErrorCode.GEJALA_NOT_FOUND,
            "duplicate_id": ErrorCode.ID_GEJALA_DUPLICATE,
            "duplicate_nama": ErrorCode.NAMA_GEJALA_DUPLICATE,
            "not_valid_id": ErrorCode.NOT_VALID_ID_GEJALA,
        }

    async def create(self, item_in: GejalaCreate) -> Gejala:
        logger.info(
            f"Creating new {self._model_name} with data: "
            f"{item_in.model_dump(exclude_unset=True)}"
        )

        await self.validate_schema(item_in)
        db_item, kelompoks = await self.build(item_in)
        self.session.add(db_item)
        db_item = await self.save(db_item)
        await self.kelompok_gejala_manager.bulks(db_item.id, list(kelompoks))
        return db_item

    async def build(self, create_schema: GejalaCreate):
        data = create_schema.model_dump(exclude_unset=True)
        kelompoks = data.pop("id_kelompok")
        return self.model(**data), set(kelompoks)

    async def validate_schema(self, item_in: GejalaCreate):
        gejalas = await self.get_all()
        if item_in.id is None:
            item_in.id = await self.create_id(gejalas)

        await self.is_valid_id(item_in.id)
        await self.is_valid_nama(gejalas, item_in.nama)
        await self.kelompok_manager.is_valid_ids(item_in.id_kelompok)

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

        code, num = data_id[:1], data_id[1:]
        if code != "G" or not num.isdigit():
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

        nums_ids = {int(pakar.id[1:]) for pakar in pakars}
        expected = set(range(min(nums_ids), max(nums_ids) + 1))
        missing_nums = expected - nums_ids

        # Assign missing IDs
        for num in sorted(missing_nums):
            new_id = f"G{num:04d}"

            if new_id not in existing_ids:
                return new_id

        # Assign new IDs for remaining entries
        next_num = max(nums_ids, default=0) + 1
        while True:
            new_id = f"G{next_num:04d}"
            if new_id not in existing_ids:
                return new_id
            next_num += 1

    async def is_valid_nama(self, pakars: Sequence[Gejala], nama: str):
        for pakar in pakars:
            if pakar.nama == nama:
                raise DuplicateNamaError(
                    "Nama di temukan sama",
                    f"Nama: {nama}",
                    status_code=status.HTTP_406_NOT_ACCEPTABLE,
                    error_code=self.error_codes["duplicate_nama"],
                )


async def get_gejala_manager(session: AsyncSession = Depends(get_async_session)):
    yield GejalaManager(session)
