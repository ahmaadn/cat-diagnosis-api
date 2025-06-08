from typing import TYPE_CHECKING

from sqlalchemy import CHAR, VARCHAR, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.mixin import TimeStampMixin

if TYPE_CHECKING:
    from app.db.models.rule import Rule


class Penyakit(TimeStampMixin, Base):
    __tablename__ = "penyakit"

    id: Mapped[str] = mapped_column(
        CHAR(5), primary_key=True, autoincrement=False, nullable=False
    )
    nama: Mapped[str] = mapped_column(
        VARCHAR(255), autoincrement=False, nullable=False, unique=True
    )
    image_url: Mapped[str] = mapped_column(VARCHAR(255), nullable=True)
    deskripsi: Mapped[str] = mapped_column(Text(), default="", nullable=True)
    solusi: Mapped[str] = mapped_column(Text(), default="", nullable=False)
    pencegahan: Mapped[str] = mapped_column(Text(), default="", nullable=True)

    rules: Mapped[list["Rule"]] = relationship(
        "Rule",
        back_populates="penyakit",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
