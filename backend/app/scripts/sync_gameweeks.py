import asyncio
from datetime import datetime
from sqlalchemy import select
from app.db import SessionLocal
from app.models.reference import GameWeek
from app.models.fixture import Fixture
from app.services.fpl import fetch_bootstrap, fetch_fixtures


async def sync_gameweeks():
    bootstrap = await fetch_bootstrap()
    events = bootstrap["events"]
    team_names = {team["id"]: team["name"] for team in bootstrap["teams"]}

    async with SessionLocal() as session:
        # --- Gameweeks ---
        gw_count = 0
        for event in events:
            result = await session.execute(
                select(GameWeek).where(GameWeek.fpl_event_id == event["id"])
            )
            gw = result.scalar_one_or_none()

            if gw is None:
                gw = GameWeek(fpl_event_id=event["id"])
                session.add(gw)

            gw.deadline_time = datetime.fromisoformat(event["deadline_time"].replace("Z", "+00:00"))
            gw.is_current = event.get("is_current", False)
            gw.is_finished = event.get("finished", False)
            gw_count += 1

        await session.flush()

        # Build fpl_event_id -> GameWeek.id lookup for fixture linking
        result = await session.execute(select(GameWeek))
        gw_lookup = {gw.fpl_event_id: gw.id for gw in result.scalars().all()}

        # --- Fixtures ---
        fixtures = await fetch_fixtures()
        fixture_count = 0
        skipped_count = 0

        for fx in fixtures:
            event_id = fx.get("event")

            if event_id is None:
                print(f"Skipping fixture {fx['id']}: no gameweek assigned yet "
                      f"({team_names.get(fx['team_h'])} vs {team_names.get(fx['team_a'])})")
                skipped_count += 1
                continue

            gameweek_id = gw_lookup.get(event_id)
            if gameweek_id is None:
                print(f"Skipping fixture {fx['id']}: gameweek {event_id} not found in our records")
                skipped_count += 1
                continue

            if fx.get("kickoff_time") is None:
                print(f"Skipping fixture {fx['id']}: no kickoff time set yet")
                skipped_count += 1
                continue

            result = await session.execute(
                select(Fixture).where(Fixture.fpl_fixture_id == fx["id"])
            )
            fixture = result.scalar_one_or_none()

            if fixture is None:
                fixture = Fixture(fpl_fixture_id=fx["id"])
                session.add(fixture)

            fixture.gameweek_id = gameweek_id
            fixture.home_team = team_names.get(fx["team_h"], "Unknown")
            fixture.away_team = team_names.get(fx["team_a"], "Unknown")
            fixture.kickoff_time = datetime.fromisoformat(fx["kickoff_time"].replace("Z", "+00:00"))
            fixture.finished = fx.get("finished", False)
            fixture_count += 1

        await session.commit()

    print(f"\nSynced {gw_count} gameweeks, {fixture_count} fixtures "
          f"({skipped_count} fixtures skipped).")


if __name__ == "__main__":
    asyncio.run(sync_gameweeks())