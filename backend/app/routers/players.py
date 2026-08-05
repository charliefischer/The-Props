from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.player import Player
from app.users import current_active_user

router = APIRouter(prefix="/players", tags=["players"])


@router.get("")
async def list_players(
    db: AsyncSession = Depends(get_db),
    user=Depends(current_active_user),
):
    result = await db.execute(select(Player).order_by(Player.team, Player.name))
    players = result.scalars().all()
    return [
        {
            "id": p.id,
            "name": p.name,
            "team": p.team,
            "position": p.position,
        }
        for p in players
    ]