from typing import TYPE_CHECKING

from sqlalchemy import CHAR, VARCHAR, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.mixin import TimeStampMixin

if TYPE_CHECKING:
    from app.db.models.rule import Rule


class Gejala(TimeStampMixin, Base):
    __tablename__ = "gejala"

    id_gejala: Mapped[str] = mapped_column(
        CHAR(5), primary_key=True, autoincrement=False, nullable=False
    )
    nama_gejala: Mapped[str] = mapped_column(
        VARCHAR(255), nullable=False, unique=True
    )

    rules: Mapped[list["Rule"]] = relationship(
        "Rule",
        back_populates="gejala",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    kelompok_gejala: Mapped["KelompokGejala"] = relationship(
        "KelompokGejala", back_populates="gejala", cascade="all, delete-orphan"
    )


class Kelompok(TimeStampMixin, Base):
    __tablename__ = "kelompok"

    id_kelompok: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True, nullable=False
    )
    nama_kelompok: Mapped[str] = mapped_column(
        VARCHAR(255), nullable=False, unique=True
    )

    kelompok_gejala: Mapped["KelompokGejala"] = relationship(
        "KelompokGejala", back_populates="kelompok", cascade="all, delete-orphan"
    )


class KelompokGejala(TimeStampMixin, Base):
    __tablename__ = "kelompok_gejala"

    id_gejala: Mapped[str] = mapped_column(
        CHAR(5),
        ForeignKey("gejala.id_gejala", ondelete="CASCADE"),
        primary_key=True,
        autoincrement=False,
        nullable=False,
    )

    id_kelompok: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("kelompok.id_kelompok", ondelete="CASCADE"),
        primary_key=True,
        autoincrement=False,
        nullable=False,
    )

    gejala: Mapped["Gejala"] = relationship(
        "Gejala", back_populates="kelompok_gejala"
    )
    kelompok: Mapped["Kelompok"] = relationship(
        "Kelompok", back_populates="kelompok_gejala"
    )
