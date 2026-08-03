from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.db import Base
from app.models import gen_uuid

class Player(Base):
    __tablename__ = "player"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    fpl_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    team: Mapped[str] = mapped_column(String(32), nullable=False)
    position: Mapped[str] = mapped_column(String(16), nullable=False)