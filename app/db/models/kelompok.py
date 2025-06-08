from sqlalchemy import VARCHAR, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.kelompok_gejala import KelompokGejala
from app.db.models.mixin import TimeStampMixin


class Kelompok(TimeStampMixin, Base):
    __tablename__ = "kelompok"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True, nullable=False
    )
    nama: Mapped[str] = mapped_column(VARCHAR(255), nullable=False, unique=True)
    deskripsi: Mapped[str] = mapped_column(Text(), default="", nullable=True)

    gejalas = relationship(
        "Gejala",
        secondary=KelompokGejala.__table__,
        back_populates="kelompoks",
        lazy="selectin",
    )
