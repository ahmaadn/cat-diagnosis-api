from fastapi import APIRouter, Depends, status
from fastapi_utils.cbv import cbv
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.sessions import get_async_session
from app.db.models.pakar import Pakar
from app.schemas.base import ResponsePayload
from app.schemas.pagination import PaginationSchema
from app.schemas.pakar import PakarCreate, PakarEdit, PakarRead
from app.utils.common import ErrorCode
from app.utils.exceptions import AppExceptionError
from app.utils.pagination import paginate

r = router = APIRouter(prefix="/pakar", tags=["Pakar"])


@cbv(router)
class PakarRouter:
    session: AsyncSession = Depends(get_async_session)

    @r.post(
        "/create",
        status_code=status.HTTP_201_CREATED,
        response_model=ResponsePayload[PakarRead],
    )
    async def create_pakar(self, pakar: PakarCreate):
        new_pakar = Pakar(**pakar.model_dump())
        self.session.add(new_pakar)
        await self.session.commit()
        await self.session.refresh(new_pakar)

        return ResponsePayload(
            message="Pakar created successfully",
            items=new_pakar,
        )

    @r.get("/all", response_model=PaginationSchema[PakarRead])
    async def get_all_pakar(self):
        return await paginate(self.session, select(Pakar), 1, 9999999)

    @r.get("/{pakar_id}", response_model=PakarRead)
    async def get_pakar_by_id(self, pakar_id: int):
        result = await self.session.execute(
            select(Pakar).where(Pakar.id_pakar == pakar_id)
        )
        pakar = result.scalar_one_or_none()
        if pakar is None:
            raise AppExceptionError(
                "Pakar not found", error_code=ErrorCode.PAKAR_NOT_FOUND
            )
        return PakarRead.model_validate(pakar)

    @r.put("/{pakar_id}/edit", response_model=PakarRead)
    async def edit_pakar_name(self, pakar_id: int, new_data: PakarEdit):
        result = await self.session.execute(
            select(Pakar).where(Pakar.id_pakar == pakar_id)
        )
        pakar = result.scalar_one_or_none()
        if pakar is None:
            raise AppExceptionError(
                "Pakar not found", error_code=ErrorCode.PAKAR_NOT_FOUND
            )

        # Update
        for key, value in new_data.model_dump().items():
            setattr(pakar, key, value)

        self.session.add(pakar)
        await self.session.commit()
        await self.session.refresh(pakar)
        return PakarRead.model_validate(pakar)
