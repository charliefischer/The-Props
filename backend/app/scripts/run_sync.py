import asyncio
from sqlalchemy import select
from app.db import SessionLocal
from app.models.reference import GameWeek
from app.scripts.sync_players import sync_players
from app.scripts.sync_gameweeks import sync_gameweeks
from app.scripts.sync_odds import sync_odds
from app.services.settlement import settle_gameweek_bets, grant_weekly_topups


async def run_full_sync():
    print("=== 1/4: Syncing players ===")
    await sync_players()

    print("\n=== 2/4: Syncing gameweeks & fixtures ===")
    await sync_gameweeks()

    print("\n=== 3/4: Syncing odds ===")
    await sync_odds()

    print("\n=== 4/4: Settlement & top-ups ===")
    async with SessionLocal() as session:
        finished = (await session.execute(
            select(GameWeek).where(GameWeek.is_finished == True)
        )).scalars().all()

        for gw in finished:
            counts = await settle_gameweek_bets(session, gw)
            if counts["settled"]:
                print(f"GW{gw.fpl_event_id}: settled {counts['settled']} "
                      f"(won={counts['won']}, lost={counts['lost']}, void={counts['void']})")

        current_gw = (await session.execute(
            select(GameWeek).where(GameWeek.is_current == True)
        )).scalar_one_or_none()

        if current_gw:
            granted = await grant_weekly_topups(session, current_gw)
            print(f"Granted top-up to {granted} membership(s).")

    print("\n=== Sync complete ===")


if __name__ == "__main__":
    asyncio.run(run_full_sync())