import asyncio
from sqlalchemy import select
from app.db import SessionLocal
from app.models.player import Player
from app.models.squad import SquadPlayer
from app.models.reference import GameWeek, PropMarket, PlayerOdds
from app.services.fpl import fetch_player_history
from app.services.odds_model import calculate_market_odds, MARKET_PREDICATES

REQUEST_DELAY_SECONDS = 0.3


async def get_squad_relevant_players(session) -> list[Player]:
    result = await session.execute(
        select(Player)
        .join(SquadPlayer, SquadPlayer.player_id == Player.id)
        .where(SquadPlayer.removed_at.is_(None))
        .distinct()
    )
    return result.scalars().all()


async def sync_odds():
    async with SessionLocal() as session:
        current_gw = (await session.execute(
            select(GameWeek).where(GameWeek.is_current == True)
        )).scalar_one_or_none()

        if not current_gw:
            print("No current gameweek set — run sync_gameweeks first.")
            return

        players = await get_squad_relevant_players(session)
        if not players:
            print("No players currently on any squad — nothing to price yet.")
            return

        markets = {m.code: m for m in (await session.execute(select(PropMarket))).scalars().all()}

        existing = (await session.execute(
            select(PlayerOdds).where(PlayerOdds.gameweek_id == current_gw.id)
        )).scalars().all()
        for row in existing:
            await session.delete(row)

        count = 0
        skipped_players = 0

        for player in players:
            try:
                history = await fetch_player_history(player.fpl_id)
            except Exception as e:
                print(f"Skipping {player.name}: could not fetch history ({e})")
                skipped_players += 1
                await asyncio.sleep(REQUEST_DELAY_SECONDS)
                continue

            for market_code in MARKET_PREDICATES:
                result = calculate_market_odds(market_code, history, player.position)
                if result is None:
                    continue

                market = markets.get(market_code)
                if market is None:
                    print(f"Skipping {market_code} for {player.name}: prop market not seeded")
                    continue

                session.add(PlayerOdds(
                    player_id=player.id,
                    gameweek_id=current_gw.id,
                    prop_market_id=market.id,
                    probability=result["probability"],
                    odds_decimal=result["odds_decimal"],
                ))
                count += 1

            await asyncio.sleep(REQUEST_DELAY_SECONDS)

        await session.commit()
        print(f"\nSynced odds for {len(players) - skipped_players}/{len(players)} players, "
              f"{count} player/market combinations, gameweek {current_gw.fpl_event_id}.")


if __name__ == "__main__":
    asyncio.run(sync_odds())