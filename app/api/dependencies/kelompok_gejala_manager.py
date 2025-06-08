import logging
from typing import Any

from fastapi import status
from sqlalchemy import exc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.kelompok_gejala import KelompokGejala
from app.schemas.kelompok import KelomopokGejalaCreate
from app.utils.base_manager import BaseManager
from app.utils.common import ErrorCode
from app.utils.exceptions import (
    AppExceptionError,
)

logger = logging.getLogger(__name__)


class KelompokGejalaManager(
    BaseManager[KelompokGejala, KelomopokGejalaCreate, KelomopokGejalaCreate]
):
    def __init__(self, session: AsyncSession):
        super().__init__(session, KelompokGejala)

    async def bulks(self, id_gejala: str, items_in: list[int]):
        for item in items_in:
            await self.create(
                input_data=KelomopokGejalaCreate(
                    id_gejala=id_gejala, id_kelompok=item
                )
            )

    async def save(self, db_item: KelompokGejala):
        id_gejala = db_item.id_gejala  # type: ignore
        id_kelompok = db_item.id_kelompok  # type: ignore
        item_id = f"{id_gejala}-{id_kelompok}"

        try:
            await self.session.commit()
            await self.session.refresh(db_item)
            logger.info(f"{self._model_name} ID Gejala: {item_id} updated.")
            return db_item

        except exc.IntegrityError as e:
            await self.session.rollback()
            logger.error(
                f"Integrity error updating {self._model_name} ID {item_id}: {e}",
                exc_info=True,
            )
            raise AppExceptionError(
                f"Failed to update {self._model_name} ID {item_id}.",
                f"Data may conflict. Detail: {e.orig}",
                status_code=status.HTTP_409_CONFLICT,
                error_code=ErrorCode.INTEGRITY_ERROR,
            ) from None
        except exc.SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(
                f"SQLAlchemy error updating {self._model_name} ID {item_id}: {e}",
                exc_info=True,
            )
            raise AppExceptionError(
                f"Failed to update {self._model_name} ID {item_id} due to db error.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error_code=ErrorCode.INTERNAL_SERVER_ERROR,
            ) from None

    async def update(self, *, item_id: Any, item_update: None) -> KelompokGejala:
        raise NotImplementedError

    async def delete_all(self, id_gejala: str):
        try:
            query = select(self.model).where(self.model.id_gejala == id_gejala)
            kelompoks = await self._execute_query(query)
            kelompoks = kelompoks.scalars().all()
            print(kelompoks)
            if not kelompoks:
                return

            for kelompok in kelompoks:
                await self.session.delete(kelompok)
                await self.session.commit()
        except exc.IntegrityError as e:
            await self.session.rollback()
            raise AppExceptionError(
                f"Failed to delete {self._model_name} ID Gejala {id_gejala} due to "
                f"integrity error. Detail: {e.orig}",
                status_code=status.HTTP_409_CONFLICT,
                error_code=ErrorCode.INTEGRITY_ERROR,
            ) from None

        except exc.SQLAlchemyError:
            await self.session.rollback()
            raise AppExceptionError(
                f"Failed to delete {self._model_name} ID Gejala {id_gejala} due to "
                "db error.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error_code=ErrorCode.INTERNAL_SERVER_ERROR,
            ) from None
