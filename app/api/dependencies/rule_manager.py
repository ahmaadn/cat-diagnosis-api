import logging
from typing import Sequence

from fastapi import Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.api.dependencies.gejala_manager import GejalaManager
from app.api.dependencies.pakar_manager import PakarManager
from app.api.dependencies.penyakit_manager import PenyakitManager
from app.api.dependencies.sessions import get_async_session
from app.db.models.rule import Rule
from app.db.models.rule_cf import RuleCf
from app.schemas.rule import RuleCfCreate, RuleCreate, RuleUpdate
from app.utils.base_manager import BaseManager
from app.utils.exceptions import AppExceptionError, DuplicateIDError, NotValidIDError
from app.utils.id_healper import IDConfig

logger = logging.getLogger(__name__)


class RuleManager(BaseManager[Rule, RuleCreate, RuleUpdate]):
    def __init__(self, session: AsyncSession):
        super().__init__(
            session,
            Rule,
            IDConfig("R", length=8, minimum_length_number=7, example="R0000001"),
            "id",
        )
        self.penyakit_manager = PenyakitManager(session)
        self.gejala_manager = GejalaManager(session)
        self.pakar_manager = PakarManager(session)

    async def create(self, input_data: RuleCreate) -> Rule:
        # Validasi bahwa Penyakit dan Gejala ada
        await self.penyakit_manager.get_by_id_or_fail(input_data.id_penyakit)
        await self.gejala_manager.get_by_id_or_fail(input_data.id_gejala)

        # Cek duplikasi rule (gejala dan penyakit yang sama)
        query = select(Rule).where(
            Rule.id_penyakit == input_data.id_penyakit,
            Rule.id_gejala == input_data.id_gejala,
        )
        existing_rule = (await self.session.execute(query)).scalars().first()
        if existing_rule:
            raise AppExceptionError(
                "Aturan dengan gejala dan penyakit yang sama sudah ada.",
                status_code=status.HTTP_409_CONFLICT,
            )

        # Generate ID unik untuk Rule
        if input_data.id is None:
            input_data.id = await self.create_id(await self.get_all())

        # validasi id
        await self.is_valid_id(input_data.id)

        return await super().create(input_data)

    async def validate_schema(self, input_data: RuleCreate):
        # Validasi bahwa Penyakit dan Gejala ada
        await self.penyakit_manager.get_by_id_or_fail(input_data.id_penyakit)
        await self.gejala_manager.get_by_id_or_fail(input_data.id_gejala)

        # Cek duplikasi rule (gejala dan penyakit yang sama)
        query = select(Rule).where(
            Rule.id_penyakit == input_data.id_penyakit,
            Rule.id_gejala == input_data.id_gejala,
        )
        existing_rule = (await self.session.execute(query)).scalars().first()
        if existing_rule:
            raise AppExceptionError(
                "Aturan dengan gejala dan penyakit yang sama sudah ada.",
                status_code=status.HTTP_409_CONFLICT,
            )

        # Generate ID unik untuk Rule
        if input_data.id is None:
            all_rules = await self.get_all(limit=9999)
            existing_ids = {r.id for r in all_rules}
            next_num = len(existing_ids) + 1
            while f"RULE{next_num:04d}" in existing_ids:
                next_num += 1
            input_data.id = f"RULE{next_num:04d}"

    async def add_or_update_cf(self, rule_id: str, cf_data: RuleCfCreate) -> Rule:
        """
        Menambahkan atau memperbarui nilai CF dari seorang pakar pada sebuah rule.
        """
        rule = await self.get_by_id_or_fail(rule_id)
        await self.pakar_manager.get_by_id_or_fail(cf_data.id_pakar)

        # Cari apakah sudah ada RuleCf untuk pakar dan rule ini
        query = select(RuleCf).where(
            RuleCf.id_rule == rule_id,
            RuleCf.id_pakar == cf_data.id_pakar,
        )
        existing_cf = (await self.session.execute(query)).scalars().first()

        if existing_cf:
            # Update jika sudah ada
            existing_cf.nilai = cf_data.nilai
            self.session.add(existing_cf)
        else:
            # Buat baru jika belum ada
            new_cf = RuleCf(
                id_rule=rule_id, id_pakar=cf_data.id_pakar, nilai=cf_data.nilai
            )
            self.session.add(new_cf)

        await self.session.commit()
        await self.session.refresh(rule)
        return rule

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

    async def create_id(self, existing_items: Sequence[Rule]) -> str:
        """
        Creates a new unique ID for a Gejala
        """
        existing_ids, nums_ids = self.id_helper.extract_numeric_ids(existing_items)
        return self.id_helper.create_id(existing_ids, nums_ids)


async def get_rule_manager(session: AsyncSession = Depends(get_async_session)):
    yield RuleManager(session)
