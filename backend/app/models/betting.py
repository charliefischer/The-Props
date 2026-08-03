from sqlalchemy import String, Float, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, timezone
from typing import Optional
from app.db import Base
from app.models import gen_uuid

class Bet(Base):
    __tablename__ = "bet"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    league_membership_id: Mapped[str] = mapped_column(String(36), ForeignKey("league_membership.id"), nullable=False)
    player_id: Mapped[str] = mapped_column(String(36), ForeignKey("player.id"), nullable=False)
    gameweek_id: Mapped[str] = mapped_column(String(36), ForeignKey("gameweek.id"), nullable=False)
    prop_market_id: Mapped[str] = mapped_column(String(36), ForeignKey("prop_market.id"), nullable=False)
    odds_decimal: Mapped[float] = mapped_column(Float, nullable=False)
    stake: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="pending")  # pending / won / lost / void
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    settled_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, default=None)


class LedgerEntry(Base):
    __tablename__ = "ledger_entry"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    league_membership_id: Mapped[str] = mapped_column(String(36), ForeignKey("league_membership.id"), nullable=False)
    bet_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("bet.id"), nullable=True)
    type: Mapped[str] = mapped_column(String(16), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    balance_after: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))