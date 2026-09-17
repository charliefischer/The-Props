from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.betting import LedgerEntry


async def get_balance(db: AsyncSession, league_membership_id: str) -> float:
    result = await db.execute(
        select(LedgerEntry.balance_after)
        .where(LedgerEntry.league_membership_id == league_membership_id)
        .order_by(desc(LedgerEntry.created_at))
        .limit(1)
    )
    row = result.scalar_one_or_none()
    return row if row is not None else 0.0