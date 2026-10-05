import secrets
import string
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.betting import LedgerEntry
from app.models.league import League, LeagueMembership
from app.models.reference import GameWeek
from app.models.user import User
from app.users import current_active_user
from app.services.leaderboard import get_leaderboard
from app.services.balance import get_balance, get_membership

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
    await db.flush()

    await db.commit()

    current_gw = (await db.execute(
        select(GameWeek).where(GameWeek.is_current == True)
    )).scalar_one_or_none()

    db.add(LedgerEntry(
        league_membership_id=membership.id,
        gameweek_id=current_gw.id if current_gw else None,
        type="starting_grant",
        amount=league.starting_credits,
        balance_after=league.starting_credits,
    ))
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
    await db.flush()

    db.add(LedgerEntry(
        league_membership_id=membership.id,
        type="starting_grant",
        amount=league.starting_credits,
        balance_after=league.starting_credits,
    ))
    await db.commit()
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

@router.get("/{league_id}/balance")
async def my_balance(
    league_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_active_user),
):
    result = await db.execute(
        select(LeagueMembership).where(
            LeagueMembership.league_id == league_id,
            LeagueMembership.user_id == user.id,
        )
    )
    membership = result.scalar_one_or_none()
    if not membership:
        raise HTTPException(403, "You are not a member of this league")

    balance = await get_balance(db, membership.id)
    return {"balance": balance}

@router.get("/{league_id}/leaderboard")
async def leaderboard(
    league_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_active_user),
):
    # Confirm the requester is actually a member before showing league data
    await get_membership(db, league_id, user.id)
    return await get_leaderboard(db, league_id)