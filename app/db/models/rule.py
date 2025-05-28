from typing import TYPE_CHECKING

from sqlalchemy import CHAR, Double, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.gejala import Gejala
from app.db.models.penyakit import Penyakit

if TYPE_CHECKING:
    from app.db.models.pakar import Pakar


class Rule(Base):
    __tablename__ = "rule"

    id_rule: Mapped[str] = mapped_column(
        CHAR(8), primary_key=True, autoincrement=False, nullable=False
    )
    id_penyakit: Mapped[str] = mapped_column(
        CHAR(5),
        ForeignKey("penyakit.id_penyakit", ondelete="CASCADE"),
        nullable=True,
    )
    id_gejala: Mapped[str] = mapped_column(
        CHAR(5), ForeignKey("gejala.id_gejala", ondelete="CASCADE"), nullable=True
    )

    penyakit: Mapped[Penyakit] = relationship("Penyakit", back_populates="rules")
    gejala: Mapped[Gejala] = relationship("Gejala", back_populates="rules")

    rule_cfs: Mapped[list["RuleCf"]] = relationship(
        "RuleCf", back_populates="rule", cascade="all, delete-orphan"
    )


class RuleCf(Base):
    __tablename__ = "rule_cf"

    id_rule: Mapped[str] = mapped_column(
        CHAR(8),
        ForeignKey("rule.id_rule", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    id_pakar: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("pakar.id_pakar", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    nilai_cf: Mapped[float] = mapped_column(Double(precision=53), nullable=False)

    rule: Mapped["Rule"] = relationship("Rule", back_populates="rule_cfs")
    pakar: Mapped["Pakar"] = relationship("Pakar", back_populates="rule_cfs")
