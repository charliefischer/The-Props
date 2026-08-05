import secrets
import string
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.league import League, LeagueMembership
from app.models.user import User
from app.users import current_active_user

router = APIRouter(prefix="/leagues", tags=["leagues"])


def generate_invite_code(length: int = 6) -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


@router.post("")
async def create_league(
    name: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_active_user),
):
    league = League(
        name=name,
        invite_code=generate_invite_code(),
        created_by=user.id,
    )
    db.add(league)
    await db.flush()

    membership = LeagueMembership(user_id=user.id, league_id=league.id)
    db.add(membership)
    await db.commit()

    return {
        "id": league.id,
        "name": league.name,
        "invite_code": league.invite_code,
    }


@router.post("/join/{invite_code}")
async def join_league(
    invite_code: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_active_user),
):
    result = await db.execute(select(League).where(League.invite_code == invite_code))
    league = result.scalar_one_or_none()

    if not league:
        raise HTTPException(404, "Invalid invite code")

    existing = await db.execute(
        select(LeagueMembership).where(
            LeagueMembership.league_id == league.id,
            LeagueMembership.user_id == user.id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Already a member of this league")

    membership = LeagueMembership(user_id=user.id, league_id=league.id)
    db.add(membership)
    await db.commit()

    return {"status": "joined", "league": league.name}


@router.get("")
async def my_leagues(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_active_user),
):
    result = await db.execute(
        select(League)
        .join(LeagueMembership, LeagueMembership.league_id == League.id)
        .where(LeagueMembership.user_id == user.id)
    )
    leagues = result.scalars().all()
    return [{"id": l.id, "name": l.name, "invite_code": l.invite_code} for l in leagues]