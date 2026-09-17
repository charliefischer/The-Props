import httpx

FPL_ROOT = "https://fantasy.premierleague.com/api/"
FPL_BOOTSTRAP_URL = f"{FPL_ROOT}bootstrap-static/"
FPL_SUMMARY_URL = f"{FPL_ROOT}element-summary/"
FPL_FIXTURE_URL = f"{FPL_ROOT}fixtures/"

POSITION_MAP = {1: "GK", 2: "DEF", 3: "MID", 4: "FWD"}

async def fetch_players() -> list[dict]:
    async with httpx.AsyncClient() as client:
        resp = await client.get(FPL_BOOTSTRAP_URL, timeout=10.0)
        resp.raise_for_status()
        data = resp.json()

    team_names = {team["id"]: team["name"] for team in data["teams"]}

    players = []
    for el in data["elements"]:
        players.append({
            "fpl_id": el["id"],
            "name": f"{el['first_name']} {el['second_name']}",
            "team": team_names[el["team"]],
            "position": POSITION_MAP[el["element_type"]],
        })
    return players

async def fetch_player_history(fpl_id: int) -> list[dict]:
    """
    Per-gameweek stats for a single player this season, from FPL's
    element-summary endpoint.
    """
    url = f"{FPL_SUMMARY_URL}{fpl_id}/"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=10.0)
        resp.raise_for_status()
        data = resp.json()
    return data.get("history", [])

async def fetch_bootstrap() -> dict:
    """Raw bootstrap-static payload — shared by players, gameweeks, teams."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(FPL_BOOTSTRAP_URL, timeout=10.0)
        resp.raise_for_status()
        return resp.json()


async def fetch_fixtures() -> list[dict]:
    async with httpx.AsyncClient() as client:
        resp = await client.get(FPL_FIXTURE_URL, timeout=10.0)
        resp.raise_for_status()
        return resp.json()