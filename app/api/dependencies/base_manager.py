from abc import ABC, abstractmethod
from typing import Generic, List, Set, Tuple, Type, TypeVar, Union

from fastapi import status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.common import ErrorCode
from app.utils.exceptions import (
    AppExceptionError,
    DuplicateIDError,
    DuplicateNamaError,
    NotValidIDError,
)

# Type variables for generic typing
ModelType = TypeVar("ModelType")  # SQLAlchemy model
CreateSchemaType = TypeVar(
    "CreateSchemaType", bound=BaseModel
)  # Pydantic create schema


class BaseManager(Generic[ModelType, CreateSchemaType], ABC):
    """
    Generic base manager class for CRUD operations with auto-ID generation.

    Args:
        ModelType: SQLAlchemy model class
        CreateSchemaType: Pydantic schema for creation
    """

    def __init__(
        self, session: AsyncSession, prefix_id: str = "", length_id: int = 5
    ):
        self.session = session
        self.prefix_id = prefix_id
        self.length_id = length_id

    # Abstract properties that must be implemented by subclasses
    @property
    @abstractmethod
    def model_class(self) -> Type[ModelType]:
        """Return the SQLAlchemy model class"""

    @property
    @abstractmethod
    def create_schema_class(self) -> Type[CreateSchemaType]:
        """Return the Pydantic create schema class"""

    @property
    @abstractmethod
    def id_field_name(self) -> str:
        """Return the name of the ID field in the model"""

    @property
    @abstractmethod
    def name_field_name(self) -> str:
        """Return the name of the name field in the model"""

    @property
    def error_codes(self):
        return {
            "duplicate_id": ErrorCode.DUPLICATE_ID,
            "duplicate_name": ErrorCode.DUPLICATE_NAMA,
            "not_valid_id": ErrorCode.NOT_VALID_ID,
        }

    async def bulks(
        self, data: List[Union[CreateSchemaType, str]]
    ) -> List[ModelType]:
        """
        Bulk create entries from a list of create schemas or string names.
        """
        try:
            entries = await self.generate_entries(data)
            return await self.saves(entries=await self.builds(entries))
        except IntegrityError:
            await self.session.rollback()
            raise AppExceptionError(
                "Integrity error occurred",
                error_code=ErrorCode.INTEGRITY_ERROR,
                status=status.HTTP_417_EXPECTATION_FAILED,
            ) from None

    async def saves(self, entries: List[ModelType]) -> List[ModelType]:
        """Save all entries to database"""
        self.session.add_all(entries)
        await self.session.commit()
        for entry in entries:
            await self.session.refresh(entry)
        return entries

    async def save(self, entry: ModelType) -> ModelType:
        """Save entry to database"""
        self.session.add(entry)
        await self.session.commit()
        await self.session.refresh(entry)
        return entry

    async def create(self, data: Union[CreateSchemaType, str]) -> ModelType:
        """Create single entry"""
        return (await self.bulks([data]))[0]

    async def build(self, data: CreateSchemaType) -> ModelType:
        """Build model instance from create schema"""
        return self.model_class(**data.model_dump())

    async def builds(self, entries: List[CreateSchemaType]) -> List[ModelType]:
        """Build multiple model instances from create schemas"""
        return [await self.build(entry) for entry in entries]

    async def fetch_all(self) -> List[ModelType]:
        """Fetch all entries ordered by ID"""
        result = await self.session.execute(select(self.model_class))
        return result.scalars().all()  # type: ignore

    async def get_existing_data(self) -> Tuple[Set[str], Set[str], Set[int]]:
        """
        Returns sets of existing IDs, names, and numeric parts of IDs.
        """
        entries = await self.fetch_all()
        ids = {getattr(entry, self.id_field_name) for entry in entries}
        names = {getattr(entry, self.name_field_name) for entry in entries}
        nums = {int(id_val[len(self.prefix_id) :]) for id_val in ids}
        return ids, names, nums

    def get_missing_ids(self, nums: Set[int]) -> Set[int]:
        """Get missing ID numbers in sequence"""
        if not nums:
            return set()
        expected = set(range(min(nums), max(nums) + 1))
        return expected - nums

    async def generate_entries(
        self, data: List[Union[str, CreateSchemaType]]
    ) -> List[CreateSchemaType]:
        """
        Validates and generates create schema objects from input data.
        """
        existing_ids, existing_names, nums_ids = await self.get_existing_data()
        duplicate_ids, duplicate_names, not_valid_ids = set(), set(), set()
        string_entries, valid_objects = [], []

        for obj in data:
            if isinstance(obj, str):
                if obj in existing_names:
                    duplicate_names.add(obj)
                else:
                    existing_names.add(obj)
                    string_entries.append(obj)
            else:
                id_val = getattr(
                    obj, self.id_field_name
                )  # Handle schema field naming
                name_val = getattr(obj, self.name_field_name)

                if id_val in existing_ids:
                    duplicate_ids.add(id_val)
                elif name_val in existing_names:
                    duplicate_names.add(name_val)
                elif not self.is_valid_id(id_val):
                    not_valid_ids.add(id_val)
                else:
                    existing_ids.add(id_val)
                    existing_names.add(name_val)
                    nums_ids.add(self.split_id(id_val)[1])
                    valid_objects.append(obj)

        self._validate_entries(duplicate_ids, duplicate_names, not_valid_ids)

        if not string_entries:
            return valid_objects

        return [
            *valid_objects,
            *self._assign_ids_to_strings(
                string_entries, existing_ids, existing_names, nums_ids
            ),
        ]

    def _validate_entries(
        self,
        duplicate_ids: Set[str],
        duplicate_names: Set[str],
        not_valid_ids: Set[str],
    ):
        """Validate entries and raise appropriate errors"""
        if duplicate_ids:
            raise DuplicateIDError(
                f"terdapat duplicate ids: {', '.join(duplicate_ids)}",
                error_code=self.error_codes["duplicate_id"],
                status=status.HTTP_406_NOT_ACCEPTABLE,
                data=list(duplicate_ids),
            )
        if duplicate_names:
            raise DuplicateNamaError(
                f"terdapat duplicate nama: {', '.join(duplicate_names)}",
                error_code=self.error_codes["duplicate_name"],
                status=status.HTTP_406_NOT_ACCEPTABLE,
                data=list(duplicate_names),
            )
        if not_valid_ids:
            raise NotValidIDError(
                f"terdapat Id yang tidak valid: {', '.join(not_valid_ids)}",
                f"Id harus diawali dengan {self.prefix_id} dan selanjutnya number contoh {self.prefix_id}0001",  # noqa: E501
                error_code=self.error_codes["not_valid_id"],
                status=status.HTTP_406_NOT_ACCEPTABLE,
                data=list(not_valid_ids),
            )

    def _assign_ids_to_strings(
        self,
        string_entries: List[str],
        existing_ids: Set[str],
        existing_names: Set[str],
        nums_ids: Set[int],
    ) -> List[CreateSchemaType]:
        """
        Assigns unique IDs to string entries, filling missing numbers first.
        """
        missing_nums = self.get_missing_ids(nums_ids)
        objs = []

        # Assign missing IDs
        for num in sorted(missing_nums):
            if not string_entries:
                break
            new_id = self.create_id(num)
            new_name = string_entries.pop(0)
            if new_id not in existing_ids:
                existing_ids.add(new_id)
                nums_ids.add(num)
                # Create schema instance dynamically
                schema_data = {
                    self.id_field_name: new_id,
                    self.name_field_name: new_name,
                }
                objs.append(self.create_schema_class(**schema_data))

        # Assign new IDs for remaining entries
        next_num = max(nums_ids, default=0) + 1
        for name in string_entries:
            new_id = self.create_id(next_num)
            if new_id not in existing_ids:
                schema_data = {
                    self.id_field_name: new_id,
                    self.name_field_name: name,
                }
                objs.append(self.create_schema_class(**schema_data))
                existing_ids.add(new_id)
                nums_ids.add(next_num)
            next_num += 1

        return objs

    def split_id(self, id_val: str) -> Tuple[str, int]:
        """Split ID into prefix and numeric parts"""
        return id_val[: len(self.prefix_id)], int(id_val[len(self.prefix_id) :])

    def create_id(self, n: int) -> str:
        """Create ID with proper formatting"""
        num_digits = self.length_id - len(self.prefix_id)
        return f"{self.prefix_id}{n:0{num_digits}d}"

    def is_valid_id(self, id: str):
        if self.length_id != len(id):
            return False

        pre_id, num = id[: len(self.prefix_id)], id[len(self.prefix_id) :]
        if pre_id != self.prefix_id:
            return False
        return num.isdigit()
