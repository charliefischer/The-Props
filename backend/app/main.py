from fastapi import FastAPI, Depends
from app.users import fastapi_users, auth_backend, current_active_user
from app.schemas.user import UserRead, UserCreate
from app.models.user import User
from app.routers import players, squad, leagues


app = FastAPI(title="Prop League API")

app.include_router(
    fastapi_users.get_auth_router(auth_backend), prefix="/auth/jwt", tags=["auth"]
)
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate), prefix="/auth", tags=["auth"]
)

@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/users/me")
async def get_me(user: User = Depends(current_active_user)):
    return {"id": user.id, "username": user.username, "email": user.email}

app.include_router(players.router)

app.include_router(squad.router)

app.include_router(leagues.router)