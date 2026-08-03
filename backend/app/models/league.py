from sqlalchemy import String, Integer, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, timezone
from app.db import Base
from app.models import gen_uuid

class League(Base):
  __tablename__ = "league"

  id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
  name: Mapped[str] = mapped_column(String(64), nullable=False)
  invite_code: Mapped[str] = mapped_column(String(16), unique=True, nullable=False)
  created_by: Mapped[str] = mapped_column(String(36), ForeignKey("user.id"), nullable=False)
  starting_credits: Mapped[int] = mapped_column(Integer, default=15)
  weekly_topup: Mapped[int] = mapped_column(Integer, default=10)
  created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

class LeagueMembership(Base):
    __tablename__ = "league_membership"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("user.id"), nullable=False)
    league_id: Mapped[str] = mapped_column(String(36), ForeignKey("league.id"), nullable=False)
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
  