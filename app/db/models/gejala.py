from typing import TYPE_CHECKING

from sqlalchemy import CHAR, VARCHAR, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.mixin import TimeStampMixin

if TYPE_CHECKING:
    from app.db.models.rule import Rule


class Gejala(TimeStampMixin, Base):
    __tablename__ = "gejala"

    id: Mapped[str] = mapped_column(
        CHAR(5), primary_key=True, autoincrement=False, nullable=False
    )
    nama: Mapped[str] = mapped_column(VARCHAR(255), nullable=False, unique=True)

    rules: Mapped[list["Rule"]] = relationship(
        "Rule",
        back_populates="gejala",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    kelompoks: Mapped[list["Kelompok"]] = relationship(
        "Kelompok",
        secondary="kelompok_gejala",
        back_populates="gejalas",
        lazy="selectin",
    )


class Kelompok(TimeStampMixin, Base):
    __tablename__ = "kelompok"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True, nullable=False
    )
    nama: Mapped[str] = mapped_column(VARCHAR(255), nullable=False, unique=True)

    gejalas: Mapped[list["Gejala"]] = relationship(
        "Gejala",
        secondary="kelompok_gejala",
        back_populates="kelompoks",
        lazy="selectin",
    )


class KelompokGejala(TimeStampMixin, Base):
    __tablename__ = "kelompok_gejala"

    id_gejala: Mapped[str] = mapped_column(
        CHAR(5),
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
