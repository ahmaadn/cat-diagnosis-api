from typing import TYPE_CHECKING

from sqlalchemy import VARCHAR, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    pass


class Rule(Base):
    __tablename__ = "rule"

    id: Mapped[str] = mapped_column(
        VARCHAR(8), primary_key=True, autoincrement=False, nullable=False
    )
    id_penyakit: Mapped[str] = mapped_column(
        VARCHAR(5),
        ForeignKey("penyakit.id", ondelete="CASCADE"),
        nullable=True,
    )
    id_gejala: Mapped[str] = mapped_column(
        VARCHAR(5), ForeignKey("gejala.id", ondelete="CASCADE"), nullable=True
    )

    penyakit = relationship("Penyakit", back_populates="rules", lazy="selectin")

    gejala = relationship("Gejala", back_populates="rules", lazy="selectin")

    rule_cfs = relationship(
        "RuleCf",
        back_populates="rule",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
