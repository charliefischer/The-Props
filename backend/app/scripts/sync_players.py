import asyncio
from sqlalchemy import select
from app.db import SessionLocal
from app.models.player import Player
from app.services.fpl import fetch_players


async def sync_players():
    players = await fetch_players()

    async with SessionLocal() as session:
        for p in players:
            result = await session.execute(select(Player).where(Player.fpl_id == p["fpl_id"]))
            existing = result.scalar_one_or_none()

            if existing:
                existing.name = p["name"]
                existing.team = p["team"]
                existing.position = p["position"]
            else:
                session.add(Player(**p))

        await session.commit()
    print(f"Synced {len(players)} players.")


if __name__ == "__main__":
    asyncio.run(sync_players())