from sqlalchemy import String, Integer, DateTime, Boolean, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, timezone
from app.db import Base
from app.models import gen_uuid

class GameWeek(Base):
    __tablename__ = "gameweek"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    fpl_event_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    deadline_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False)
    is_finished: Mapped[bool] = mapped_column(Boolean, default=False)


class PropMarket(Base):
    __tablename__ = "prop_market"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(64), nullable=False)

class PlayerOdds(Base):
    __tablename__ = "player_odds"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    player_id: Mapped[str] = mapped_column(String(36), ForeignKey("player.id"), nullable=False)
    gameweek_id: Mapped[str] = mapped_column(String(36), ForeignKey("gameweek.id"), nullable=False)
    prop_market_id: Mapped[str] = mapped_column(String(36), ForeignKey("prop_market.id"), nullable=False)
    probability: Mapped[float] = mapped_column(Float, nullable=False)
    odds_decimal: Mapped[float] = mapped_column(Float, nullable=False)
    computed_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))