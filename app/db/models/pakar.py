from sqlalchemy import VARCHAR, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.mixin import TimeStampMixin
from app.db.models.rule import RuleCf


class Pakar(TimeStampMixin, Base):
    __tablename__ = "pakar"

    id_pakar: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True, nullable=False
    )
    nama_pakar: Mapped[str] = mapped_column(
        VARCHAR(100), autoincrement=False, nullable=False
    )

    rule_cfs: Mapped[list[RuleCf]] = relationship("RuleCf", back_populates="pakar")
