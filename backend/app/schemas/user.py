import uuid
from fastapi_users import schemas

class UserRead(schemas.BaseUser[str]):
    username: str

class UserCreate(schemas.BaseUserCreate):
    username: str

class UserUpdate(schemas.BaseUserUpdate):
    username: str | None = None