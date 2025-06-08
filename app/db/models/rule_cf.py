from typing import TYPE_CHECKING

from sqlalchemy import CHAR, VARCHAR, Double, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    pass


class RuleCf(Base):
    __tablename__ = "rule_cf"

    id_rule: Mapped[str] = mapped_column(
        VARCHAR(8),
        ForeignKey("rule.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    id_pakar: Mapped[str] = mapped_column(
        CHAR(5),
        ForeignKey("pakar.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    nilai: Mapped[float] = mapped_column(Double(precision=53), nullable=False)

    rule = relationship("Rule", back_populates="rule_cfs")
    pakar = relationship("Pakar", back_populates="rule_cfs")
