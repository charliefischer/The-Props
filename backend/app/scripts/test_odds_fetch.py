import asyncio
import json
from app.services.odds_api import fetch_match_odds


async def main():
    matches = await fetch_match_odds()
    print(f"\nFetched {len(matches)} matches.\n")
    if matches:
        print(json.dumps(matches[0], indent=2))


if __name__ == "__main__":
    asyncio.run(main())