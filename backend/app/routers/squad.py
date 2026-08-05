from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

from app.db import get_db
from app.models.squad import SquadPlayer
from app.models.player import Player
from app.models.user import User
from app.users import current_active_user

router = APIRouter(prefix="/squad", tags=["squad"])

MAX_SQUAD_SIZE = 15


async def get_active_squad(db: AsyncSession, user_id: str) -> list[SquadPlayer]:
    result = await db.execute(
        select(SquadPlayer).where(
            SquadPlayer.user_id == user_id,
            SquadPlayer.removed_at.is_(None),
        )
    )
    return result.scalars().all()


@router.get("")
async def get_squad(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_active_user),
):
    active = await get_active_squad(db, user.id)
    player_ids = [sp.player_id for sp in active]

    if not player_ids:
        return []

    result = await db.execute(select(Player).where(Player.id.in_(player_ids)))
    players = result.scalars().all()
    return [{"id": p.id, "name": p.name, "team": p.team, "position": p.position} for p in players]


@router.post("/add/{player_id}")
async def add_player(
    player_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_active_user),
):
    player = await db.get(Player, player_id)
    if not player:
        raise HTTPException(404, "Player not found")

    active = await get_active_squad(db, user.id)

    if len(active) >= MAX_SQUAD_SIZE:
        raise HTTPException(400, f"Squad is full ({MAX_SQUAD_SIZE} players max)")

    if any(sp.player_id == player_id for sp in active):
        raise HTTPException(400, "Player already in squad")

    squad_player = SquadPlayer(user_id=user.id, player_id=player_id)
    db.add(squad_player)
    await db.commit()
    return {"status": "added", "player": player.name}


@router.delete("/remove/{player_id}")
async def remove_player(
    player_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_active_user),
):
    active = await get_active_squad(db, user.id)
    squad_player = next((sp for sp in active if sp.player_id == player_id), None)

    if not squad_player:
        raise HTTPException(404, "Player not in your active squad")

    squad_player.removed_at = datetime.now(timezone.utc)
    await db.commit()
    return {"status": "removed"}