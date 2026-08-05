import httpx

FPL_BOOTSTRAP_URL = "https://fantasy.premierleague.com/api/bootstrap-static/"

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