from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.betting import LedgerEntry
from fastapi import HTTPException
from app.models.league import LeagueMembership


async def get_balance(db: AsyncSession, league_membership_id: str) -> float:
    result = await db.execute(
        select(LedgerEntry.balance_after)
        .where(LedgerEntry.league_membership_id == league_membership_id)
        .order_by(desc(LedgerEntry.created_at))
        .limit(1)
    )
    row = result.scalar_one_or_none()
    return row if row is not None else 0.0

async def get_membership(db: AsyncSession, league_id: str, user_id: str) -> LeagueMembership:
    result = await db.execute(
        select(LeagueMembership).where(
            LeagueMembership.league_id == league_id,
            LeagueMembership.user_id == user_id,
        )
    )
    membership = result.scalar_one_or_none()
    if not membership:
        raise HTTPException(403, "You are not a member of this league")
    return membership