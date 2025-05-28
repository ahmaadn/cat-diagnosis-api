from fastapi import Depends, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.sessions import get_async_session
from app.db.models.penyakit import Penyakit
from app.schemas.penyakit import PenyakitCreate
from app.utils.common import ErrorCode
from app.utils.exceptions import (
    AppExceptionError,
    DuplicateIDPenyakitError,
    NotValidIDError,
)
from app.utils.generate_id import is_valid_id


class PenyakitManager:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def bulks(self, data: list[PenyakitCreate | str]):
        try:
            penyakit_entries = await self.create_penyakit_entries(data)
            new_penyakits = [
                Penyakit(**item.model_dump()) for item in penyakit_entries
            ]
            self.session.add_all(new_penyakits)
            await self.session.commit()
            for p in new_penyakits:
                await self.session.refresh(p)
            return new_penyakits
        except IntegrityError:
            await self.session.rollback()
            raise AppExceptionError(
                "Integrity error occurred",
                error_code=ErrorCode.INTEGRITY_ERROR,
                status=status.HTTP_417_EXPECTATION_FAILED,
            ) from None

    async def create(self, data: PenyakitCreate | str):
        return await self.bulks([data])

    async def delete(self, data: ...): ...

    async def get_ids_penyakit(self) -> tuple[set[str], set[int]]:
        result = await self.session.execute(
            select(Penyakit.id_penyakit).order_by(Penyakit.id_penyakit.asc())
        )
        ids = list(result.scalars().all())
        nums = {int(id[1:]) for id in ids}
        return set(ids), nums

    async def get_missing_ids(self, nums: set[int]) -> set[int]:
        if not nums:
            return set()
        expected = set(range(min(nums), max(nums) + 1))
        return expected - nums

    async def create_penyakit_entries(
        self, data: list[str | PenyakitCreate]
    ) -> list[PenyakitCreate]:
        existing_ids, nums = await self.get_ids_penyakit()
        penyakit_strs = []
        penyakit_objs = []
        duplicate_ids = []

        for p in data:
            if isinstance(p, str):
                penyakit_strs.append(p)
                continue

            if isinstance(p, PenyakitCreate):
                id = p.id_penyakit
                if id in existing_ids:
                    duplicate_ids.append(id)
                    continue

                if is_valid_id(id, prefix="P", length=5):
                    raise NotValidIDError(
                        f"Id {id} is not valid",
                        error_code=ErrorCode.NOT_VALID_ID,
                        status=status.HTTP_406_NOT_ACCEPTABLE,
                    )

                existing_ids.add(id)
                nums.add(int(id[1:]))
                penyakit_objs.append(p)
                continue

        if duplicate_ids:
            raise DuplicateIDPenyakitError(
                f"terdapat duplicate ids: {duplicate_ids!s}",
                error_code=ErrorCode.DUPLICATE_ID,
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )

        return await self._assign_ids_to_strings(
            penyakit_strs, penyakit_objs, existing_ids, nums
        )

    async def _assign_ids_to_strings(
        self,
        penyakit_strs: list[str],
        penyakit_objs: list[PenyakitCreate],
        existing_ids: set[str],
        nums: set[int],
    ) -> list[PenyakitCreate]:
        missing_nums = await self.get_missing_ids(nums)

        for num in sorted(missing_nums):
            if not penyakit_strs:
                break

            new_id = f"P{num:04d}"

            if new_id not in existing_ids:
                name = penyakit_strs.pop(0)
                existing_ids.add(new_id)
                nums.add(num)
                penyakit_objs.append(
                    PenyakitCreate(id_penyakit=new_id, nama_penyakit=name)
                )

        i = max(nums, default=0) + 1
        while penyakit_strs:
            id = f"P{i:04d}"
            if id not in existing_ids:
                p = penyakit_strs.pop()
                existing_ids.add(id)
                nums.add(i)
                penyakit_objs.append(PenyakitCreate(id_penyakit=id, nama_penyakit=p))

            i += 1
            if not penyakit_strs:
                break

        return penyakit_objs

    def is_valid_id(self, id: str, prefix: str = "P", length: int = 5):
        if len(prefix) > len(id) or length > len(id):
            return False

        pre_id, num = id[: len(prefix)], id[len(prefix) :]
        if pre_id != prefix:
            return False
        if not num.isdigit():
            return False

        return len(id) == length

    def _create_new_id(self): ...


def get_penyakit_manager(session: AsyncSession = Depends(get_async_session)):
    """
    Dependency function that provides an instance of PenyakitManager
    using the given database session.
    """
    yield PenyakitManager(session)
