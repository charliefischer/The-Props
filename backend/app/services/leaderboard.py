from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.league import LeagueMembership
from app.models.user import User
from app.models.betting import LedgerEntry
from app.services.balance import get_balance


async def get_leaderboard(db: AsyncSession, league_id: str) -> list[dict]:
    memberships = (await db.execute(
        select(LeagueMembership, User)
        .join(User, User.id == LeagueMembership.user_id)
        .where(LeagueMembership.league_id == league_id)
    )).all()

    rows = []
    for membership, user in memberships:
        balance = await get_balance(db, membership.id)

        total_funded = (await db.execute(
            select(func.coalesce(func.sum(LedgerEntry.amount), 0.0))
            .where(
                LedgerEntry.league_membership_id == membership.id,
                LedgerEntry.type.in_(["starting_grant", "topup"]),
            )
        )).scalar_one()

        rows.append({
            "user_id": user.id,
            "username": user.username,
            "balance": round(balance, 2),
            "total_funded": round(total_funded, 2),
            "profit": round(balance - total_funded, 2),
        })

    rows.sort(key=lambda r: r["profit"], reverse=True)
    return rows