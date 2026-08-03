from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from fastapi_users.db import SQLAlchemyBaseUserTable
from app.db import Base
from app.models import gen_uuid

class User(SQLAlchemyBaseUserTable[str], Base):
  __tablename__ = "user"

  id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
  username: Mapped[str] = mapped_column(String(36), unique=True, nullable=False)