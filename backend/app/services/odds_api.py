import httpx
from app.config import ODDS_API_KEY, ODDS_API_BASE_URL

SPORT_KEY = "soccer_epl"


async def fetch_match_odds() -> list[dict]:
    """
    Fetch upcoming Premier League match odds (head-to-head and totals)
    from The Odds API's free tier.
    """
    url = f"{ODDS_API_BASE_URL}/sports/{SPORT_KEY}/odds"
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": "uk",
        "markets": "h2h,totals",
        "oddsFormat": "decimal",
    }

    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params, timeout=10.0)
        resp.raise_for_status()
        matches = resp.json()

    print(f"Odds API usage — remaining: {resp.headers.get('x-requests-remaining')}, "
          f"used: {resp.headers.get('x-requests-used')}")

    return matches