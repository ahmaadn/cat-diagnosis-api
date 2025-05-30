from typing import List

from fastapi import Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.base_manager import BaseManager
from app.api.dependencies.sessions import get_async_session
from app.db.models.gejala import Kelompok
from app.schemas.gejala import KelompokCreate
from app.utils.exceptions import DuplicateNamaError


class KelompokManager(BaseManager[Kelompok, KelompokCreate]):
    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def get_existing_data(self):
        data = await self.fetch_all()
        return [name.nama_kelompok for name in data]

    async def generate_entries(
        self, data: List[str | KelompokCreate]
    ) -> List[KelompokCreate]:
        existing_name = await self.get_existing_data()
        objs, duplicate_name = [], []
        objs = []
        for obj in data:
            if isinstance(obj, str):
                if obj in existing_name:
                    duplicate_name.append(obj)
                else:
                    objs.append(self.create_schema_class(nama_kelompok=obj))
                    existing_name.append(obj)
            elif obj.nama_kelompok in existing_name:
                duplicate_name.append(obj.nama_kelompok)
            else:
                objs.append(obj)
                existing_name.append(obj.nama_kelompok)

        self._validate_entries(duplicate_name)
        return objs

    def _validate_entries(self, duplicate_name: list[str]):
        if duplicate_name:
            raise DuplicateNamaError(
                f"terdapat duplicate nama: {', '.join(duplicate_name)}",
                error_code=self.error_codes["duplicate_name"],
                status=status.HTTP_406_NOT_ACCEPTABLE,
                data=list(duplicate_name),
            )

    async def is_existing(self, nama: str):
        _is = await self.session.execute(
            select(Kelompok).where(Kelompok.nama_kelompok == nama)
        )
        return _is.one_or_none()

    @property
    def model_class(self):
        return Kelompok

    @property
    def create_schema_class(self):
        return KelompokCreate

    @property
    def id_field_name(self):
        return "id_penyakit"

    @property
    def name_field_name(self):
        return "nama_penyakit"


def get_kelompok_manager(session: AsyncSession = Depends(get_async_session)):
    """
    Dependency function that provides an instance of PenyakitManager
    using the given database session.
    """
    yield KelompokManager(session)
