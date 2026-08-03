from sqlalchemy import String, Integer, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
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