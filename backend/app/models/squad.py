from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, timezone
from typing import Optional
from app.db import Base
from app.models import gen_uuid

class SquadPlayer(Base):
    __tablename__ = "squad_player"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("user.id"), nullable=False)
    player_id: Mapped[str] = mapped_column(String(36), ForeignKey("player.id"), nullable=False)
    added_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    removed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, default=None)