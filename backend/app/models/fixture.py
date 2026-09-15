from sqlalchemy import String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.db import Base
from app.models import gen_uuid

class Fixture(Base):
    __tablename__ = "fixture"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    gameweek_id: Mapped[str] = mapped_column(String(36), ForeignKey("gameweek.id"), nullable=False)
    fpl_fixture_id: Mapped[int] = mapped_column(unique=True, nullable=False)
    home_team: Mapped[str] = mapped_column(String(32), nullable=False)
    away_team: Mapped[str] = mapped_column(String(32), nullable=False)
    kickoff_time: Mapped[DateTime] = mapped_column(DateTime, nullable=False)
    finished: Mapped[bool] = mapped_column(Boolean, default=False)