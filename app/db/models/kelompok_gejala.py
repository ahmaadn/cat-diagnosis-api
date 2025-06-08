from sqlalchemy import VARCHAR, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class KelompokGejala(Base):
    __tablename__ = "kelompok_gejala"

    id_gejala: Mapped[str] = mapped_column(
        VARCHAR(5),
        ForeignKey("gejala.id", ondelete="CASCADE"),
        primary_key=True,
        autoincrement=False,
        nullable=False,
    )

    id_kelompok: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("kelompok.id", ondelete="CASCADE"),
        primary_key=True,
        autoincrement=False,
        nullable=False,
    )
