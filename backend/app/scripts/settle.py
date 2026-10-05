import asyncio
from sqlalchemy import select
from app.db import SessionLocal
from app.models.reference import GameWeek
from app.services.settlement import settle_gameweek_bets, grant_weekly_topups


async def main():
    async with SessionLocal() as session:
        finished = (await session.execute(
            select(GameWeek).where(GameWeek.is_finished == True)
        )).scalars().all()

        for gw in finished:
            counts = await settle_gameweek_bets(session, gw)
            if counts["settled"]:
                print(f"GW{gw.fpl_event_id}: settled {counts['settled']} "
                      f"(won={counts['won']}, lost={counts['lost']}, void={counts['void']}, "
                      f"errors={counts['errors']})")

        current_gw = (await session.execute(
            select(GameWeek).where(GameWeek.is_current == True)
        )).scalar_one_or_none()

        if current_gw:
            granted = await grant_weekly_topups(session, current_gw)
            print(f"Granted top-up to {granted} membership(s) for GW{current_gw.fpl_event_id}.")


if __name__ == "__main__":
    asyncio.run(main())