import asyncio
from sqlalchemy import select
from app.db import SessionLocal
from app.models.reference import PropMarket

MARKETS = [
    ("yellow_card", "Yellow card"),
    ("red_card", "Red card"),
    ("anytime_scorer", "Anytime goalscorer"),
    ("assist", "Assist"),
    ("defensive_actions_5plus", "5+ defensive actions"),
    ("clean_sheet", "Clean sheet"),
    ("saves_3plus", "3+ saves"),
    ("team_win", "Team to win"),
    ("team_draw", "Match to be a draw"),
]


async def seed():
    async with SessionLocal() as session:
        for code, display_name in MARKETS:
            result = await session.execute(select(PropMarket).where(PropMarket.code == code))
            if not result.scalar_one_or_none():
                session.add(PropMarket(code=code, display_name=display_name))
        await session.commit()
    print(f"Seeded {len(MARKETS)} prop markets.")


if __name__ == "__main__":
    asyncio.run(seed())