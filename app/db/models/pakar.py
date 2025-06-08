from sqlalchemy import CHAR, VARCHAR
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.mixin import TimeStampMixin


class Pakar(TimeStampMixin, Base):
    __tablename__ = "pakar"

    id: Mapped[str] = mapped_column(
        CHAR(5), primary_key=True, unique=True, nullable=False
    )
    nama: Mapped[str] = mapped_column(
        VARCHAR(100), autoincrement=False, nullable=False, unique=True
    )

    # rule_cfs: Mapped[list[RuleCf]] = relationship("RuleCf", back_populates="pakar")
