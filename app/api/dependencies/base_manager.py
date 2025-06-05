import logging
from typing import Any, Generic, List, Optional, Type, TypeVar

from fastapi import status
from pydantic import BaseModel
from sqlalchemy import exc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql.expression import func

from app.utils.common import ErrorCode
from app.utils.exceptions import AppExceptionError, NotValidIDError

logger = logging.getLogger(__name__)

ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseManager(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Generic base class for CRUD and bulk operations on SQLAlchemy models.
    Uses AppExceptionError for error handling.
    """

    def __init__(self, session: AsyncSession, model: Type[ModelType]):
        if not model:
            raise ValueError("SQLAlchemy model must be provided.")
        self.session = session
        self.model = model
        self._model_name = self.model.__name__

    async def _execute_query(self, query):
        try:
            return await self.session.execute(query)
        except exc.SQLAlchemyError as e:
            logger.error(
                f"SQLAlchemy error executing query for {self._model_name}: {e}",
                exc_info=True,
            )
            raise AppExceptionError(
                f"Internal db error accessing {self._model_name}.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error_code=ErrorCode.INTERNAL_SERVER_ERROR,
            ) from None
        except Exception as e:
            logger.error(
                f"Unexpected error executing query for {self._model_name}: {e}",
                exc_info=True,
            )
            raise AppExceptionError(
                f"Unexpected error accessing {self._model_name}.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error_code=ErrorCode.INTERNAL_SERVER_ERROR,
            ) from None

    async def get_all(self, *, skip: int = 0, limit: int = 100) -> List[ModelType]:
        logger.debug(f"Fetching all {self._model_name} (skip={skip}, limit={limit})")
        query = select(self.model).offset(skip).limit(limit)
        result = await self._execute_query(query)
        return result.scalars().all()  # type: ignore

    async def get_by_id(self, item_id: Any) -> Optional[ModelType]:
        logger.debug(f"Fetching {self._model_name} by ID: {item_id}")
        query = select(self.model).where(self.model.id == item_id)  # type: ignore
        result = await self._execute_query(query)
        instance = result.scalars().first()
        if not instance:
            logger.info(f"{self._model_name} with ID '{item_id}' not found.")
        return instance

    async def get_by_id_or_fail(self, item_id: Any) -> ModelType:
        instance = await self.get_by_id(item_id)
        if not instance:
            raise NotValidIDError(
                f"{self._model_name} with ID '{item_id}' not found.",
                status_code=status.HTTP_404_NOT_FOUND,
                error_code=self.error_codes["not_valid_id"],
            )
        return instance

    @property
    def error_codes(self):
        return {
            "not_found": ErrorCode.NOT_FOUND,
            "duplicate_id": ErrorCode.DUPLICATE_ID,
            "duplicate_nama": ErrorCode.DUPLICATE_NAMA,
            "not_valid_id": ErrorCode.NOT_VALID_ID,
        }

    async def create(self, item_in: CreateSchemaType) -> ModelType:
        logger.info(
            f"Creating new {self._model_name} with data: "
            f"{item_in.model_dump(exclude_unset=True)}"
        )

        await self.validate_schema(item_in)
        db_item = await self.build(item_in)
        self.session.add(db_item)
        return await self.save(db_item)

    async def validate_schema(self, item_in: CreateSchemaType): ...

    async def update(
        self, *, item_id: Any, item_update: UpdateSchemaType
    ) -> ModelType:
        logger.info(
            f"Updating {self._model_name} ID: {item_id}, "
            f"data: {item_update.model_dump(exclude_unset=True)}"
        )

        db_item = await self.get_by_id_or_fail(item_id)
        update_data = item_update.model_dump(exclude_unset=True)
        valid_update_data = await self._validate_update(db_item, update_data)

        return await self._update(db_item, valid_update_data)

    async def _validate_update(
        self, db_item: ModelType, update_data: dict[str, Any]
    ):
        validated_update_dict = {}
        for field, value in update_data.items():
            if hasattr(db_item, field):
                validated_update_dict[field] = value
            else:
                logger.warning(
                    f"Field '{field}' not found on {self._model_name} during update."
                )
        return validated_update_dict

    async def _update(self, db_item: ModelType, update_dict: dict[str, Any]):
        for field, value in update_dict.items():
            setattr(db_item, field, value)

        self.session.add(db_item)
        return await self.save(db_item)

    async def delete(self, *, item_id: Any) -> ModelType:
        logger.info(f"Deleting {self._model_name} ID: {item_id}")
        db_item = await self.get_by_id_or_fail(item_id)
        try:
            await self.session.delete(db_item)
            await self.session.commit()
            logger.info(f"{self._model_name} ID: {item_id} deleted.")
            return db_item
        except exc.IntegrityError as e:
            await self.session.rollback()
            logger.error(
                f"Integrity error deleting {self._model_name} ID {item_id}: {e}",
                exc_info=True,
            )
            if "foreign key constraint" in str(e.orig).lower():
                raise AppExceptionError(
                    f"Cannot delete {self._model_name} ID "
                    f"{item_id} due to related data.",
                    status_code=status.HTTP_409_CONFLICT,
                    error_code=ErrorCode.INTEGRITY_ERROR,
                ) from None
            raise AppExceptionError(
                f"Failed to delete {self._model_name} ID {item_id} due to "
                f"integrity error. Detail: {e.orig}",
                status_code=status.HTTP_409_CONFLICT,
                error_code=ErrorCode.INTEGRITY_ERROR,
            ) from None

        except exc.SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(
                f"SQLAlchemy error deleting {self._model_name} ID {item_id}: {e}",
                exc_info=True,
            )
            raise AppExceptionError(
                f"Failed to delete {self._model_name} ID {item_id} due to db error.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error_code=ErrorCode.INTERNAL_SERVER_ERROR,
            ) from None

    async def count(self) -> int:
        logger.debug(f"Counting {self._model_name}")
        query = select(func.count()).select_from(self.model)
        result = await self._execute_query(query)
        total = result.scalar_one_or_none()
        return total or 0

    async def bulk(self, *, items_in: List[CreateSchemaType]) -> List[ModelType]:
        logger.info(f"Bulk creating {len(items_in)} {self._model_name} items.")
        if not items_in:
            return []

        for item in items_in:
            await self.validate_schema(item_in=item)

        db_items = [
            self.model(**item.model_dump(exclude_unset=True)) for item in items_in
        ]
        self.session.add_all(db_items)
        try:
            await self.session.commit()
            for item in db_items:
                await self.session.refresh(item)
            logger.info(f"Bulk created {len(db_items)} {self._model_name} items.")
            return db_items
        except exc.IntegrityError as e:
            await self.session.rollback()
            logger.error(
                f"Integrity error during bulk create {self._model_name}: {e}",
                exc_info=True,
            )
            raise AppExceptionError(
                f"Bulk create failed for {self._model_name} due to integrity error. "
                f"All items rolled back. Detail: {e.orig}",
                status_code=status.HTTP_409_CONFLICT,
                error_code=ErrorCode.INTEGRITY_ERROR,
            ) from None
        except exc.SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(
                f"SQLAlchemy error during bulk create {self._model_name}: {e}",
                exc_info=True,
            )
            raise AppExceptionError(
                f"Bulk create failed for {self._model_name} due to db error. "
                f"All items rolled back.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error_code=ErrorCode.INTERNAL_SERVER_ERROR,
            ) from None

    async def build(self, create_schema: CreateSchemaType) -> ModelType:
        data = create_schema.model_dump(exclude_unset=True)
        return self.model(**data)

    async def save(self, db_item: ModelType) -> ModelType:
        item_id = db_item.id  # type: ignore

        try:
            await self.session.commit()
            await self.session.refresh(db_item)
            logger.info(f"{self._model_name} ID: {item_id} updated.")
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
