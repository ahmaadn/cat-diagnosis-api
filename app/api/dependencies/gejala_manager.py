import logging
from typing import Any, Sequence

from fastapi import Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.kelompok_gejala_manager import KelompokGejalaManager
from app.api.dependencies.kelompok_manager import KelompokManager
from app.api.dependencies.sessions import get_async_session
from app.db.models.gejala import Gejala
from app.schemas.gejala import GejalaCreate, GejalaUpdate
from app.utils.base_manager import BaseManager
from app.utils.common import ErrorCode
from app.utils.exceptions import (
    DuplicateIDError,
    DuplicateNamaError,
    NotValidIDError,
)
from app.utils.id_healper import IDConfig

logger = logging.getLogger(__name__)


class GejalaManager(BaseManager[Gejala, GejalaCreate, GejalaUpdate]):
    """Manager for handling Gejala (Symptom) entities"""

    def __init__(self, session: AsyncSession):
        super().__init__(
            session,
            Gejala,
            id_config=IDConfig(
                prefix="G", length=5, numeric_length=4, example="G0001"
            ),
        )
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

    async def create(self, input_data: GejalaCreate) -> Gejala:
        logger.info(
            f"Creating new {self._model_name} with data: "
            f"{input_data.model_dump(exclude_unset=True)}"
        )

        # valiasi schma create
        await self.validate_schema(input_data)

        db_item, kelompoks = await self.build(input_data)
        self.session.add(db_item)
        await self.save(db_item)

        # Create relasi gejala dengan kelomook
        await self.kelompok_gejala_manager.bulks(db_item.id, list(kelompoks))
        await self.session.refresh(db_item)
        return db_item

    async def update(self, *, item_id: Any, item_update: GejalaUpdate) -> Gejala:
        db_item = await self.get_by_id_or_fail(item_id)

        update_data = item_update.model_dump(exclude_unset=True)
        kelompoks = update_data.pop("kelompoks", None)
        if kelompoks is not None:
            # Validasi kelompok
            await self.kelompok_manager.is_valid_ids(kelompoks)

        valid_update_data = await self._validate_update(db_item, update_data)
        print(update_data)

        db_item = await self._update(db_item, valid_update_data)
        if kelompoks is not None:
            await self.kelompok_gejala_manager.delete_all(db_item.id)
            await self.kelompok_gejala_manager.bulks(db_item.id, kelompoks)

        await self.session.refresh(db_item)
        return db_item

    async def build(self, create_schema: GejalaCreate) -> tuple[Gejala, set[int]]:
        data = create_schema.model_dump(exclude_unset=True)
        kelompoks = data.pop("kelompoks", [])
        return self.model(**data), set(kelompoks)

    async def validate_schema(self, item_in: GejalaCreate):
        gejalas = await self.get_all(limit=200)
        if item_in.id is None:
            item_in.id = await self.create_id(gejalas)

        # validasi id
        await self.is_valid_id(item_in.id)

        # validasi nama gejala
        await self.is_valid_nama(gejalas, item_in.nama)

        # validasi kelompoks
        await self.kelompok_manager.is_valid_ids(item_in.kelompoks)

    async def is_valid_id(self, data_id: str) -> None:
        """
        Validates a Gejala ID
        Raises appropriate exceptions if validation fails
        """
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

    async def create_id(self, existing_items: Sequence[Gejala]) -> str:
        """
        Creates a new unique ID for a Gejala
        """
        existing_ids, nums_ids = self.id_helper.extract_numeric_ids(existing_items)
        return self.id_helper.create_id(existing_ids, nums_ids)

    async def is_valid_nama(self, items: Sequence[Gejala], nama: str) -> None:
        """
        Validates a Gejala name is unique
        Args:
            items: Existing items to check against
            nama: Name to validate
        Raises:
            DuplicateNamaError: If name already exists
        """
        if any(item.nama == nama for item in items):
            raise DuplicateNamaError(
                f"Nama: {nama} telah terdaftar",
                "Gunakan nama yang berbeda",
                error_code=self.error_codes["duplicate_nama"],
                status_code=status.HTTP_406_NOT_ACCEPTABLE,
            )


async def get_gejala_manager(session: AsyncSession = Depends(get_async_session)):
    yield GejalaManager(session)
