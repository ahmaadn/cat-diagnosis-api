from typing import TYPE_CHECKING

from sqlalchemy import CHAR, VARCHAR, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.kelompok_gejala import KelompokGejala
from app.db.models.mixin import TimeStampMixin

if TYPE_CHECKING:
    pass


class Gejala(TimeStampMixin, Base):
    __tablename__ = "gejala"

    id: Mapped[str] = mapped_column(
        CHAR(5), primary_key=True, autoincrement=False, nullable=False
    )
    nama: Mapped[str] = mapped_column(VARCHAR(255), nullable=False, unique=True)
    image_url: Mapped[str] = mapped_column(VARCHAR(255), nullable=True)
    deskripsi: Mapped[str] = mapped_column(Text(), default="", nullable=True)
    pertanyaan: Mapped[str] = mapped_column(Text(), default="", nullable=False)

    rules = relationship(
        "Rule",
        back_populates="gejala",
        cascade="all, delete-orphan",
    )

    kelompoks = relationship(
        "Kelompok",
        secondary=KelompokGejala.__table__,
        back_populates="gejalas",
        lazy="selectin",
    )
