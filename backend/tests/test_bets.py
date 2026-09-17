from sqlalchemy import select
from app.models.reference import GameWeek, PropMarket, PlayerOdds


async def create_league_with_squad_and_odds(client, db_session, auth_headers, make_player):
    """Shared setup: a league, a squad player, and priced odds for them."""
    resp = await client.post("/leagues?name=Bet Test League", headers=auth_headers)
    league_id = resp.json()["id"]

    player = await make_player(position="DEF")
    await client.post(f"/squad/add/{player.id}", headers=auth_headers)

    market = (await db_session.execute(
        select(PropMarket).where(PropMarket.code == "yellow_card")
    )).scalar_one()
    gw = (await db_session.execute(
        select(GameWeek).where(GameWeek.is_current == True)
    )).scalar_one()

    db_session.add(PlayerOdds(
        player_id=player.id,
        gameweek_id=gw.id,
        prop_market_id=market.id,
        probability=0.2,
        odds_decimal=4.5,
    ))
    await db_session.commit()

    return league_id, player


class TestBets:
    async def test_place_bet_succeeds(self, client, db_session, auth_headers, make_player):
        league_id, player = await create_league_with_squad_and_odds(
            client, db_session, auth_headers, make_player
        )
        resp = await client.post(f"/leagues/{league_id}/bets", headers=auth_headers, json={
            "player_id": player.id, "prop_market_code": "yellow_card", "stake": 2,
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body["odds_decimal"] == 4.5
        assert body["stake"] == 2
        assert body["balance_after"] == 13  # 15 starting - 2 stake

    async def test_duplicate_bet_fails(self, client, db_session, auth_headers, make_player):
        league_id, player = await create_league_with_squad_and_odds(
            client, db_session, auth_headers, make_player
        )
        payload = {"player_id": player.id, "prop_market_code": "yellow_card", "stake": 2}
        first = await client.post(f"/leagues/{league_id}/bets", headers=auth_headers, json=payload)
        assert first.status_code == 200

        second = await client.post(f"/leagues/{league_id}/bets", headers=auth_headers, json=payload)
        assert second.status_code == 400

    async def test_insufficient_balance_fails(self, client, db_session, auth_headers, make_player):
        league_id, player = await create_league_with_squad_and_odds(
            client, db_session, auth_headers, make_player
        )
        resp = await client.post(f"/leagues/{league_id}/bets", headers=auth_headers, json={
            "player_id": player.id, "prop_market_code": "yellow_card", "stake": 999,
        })
        assert resp.status_code == 400

    async def test_bet_on_player_not_in_squad_fails(self, client, db_session, auth_headers, make_player):
        resp = await client.post("/leagues?name=No Squad League", headers=auth_headers)
        league_id = resp.json()["id"]

        other_player = await make_player()  # never added to squad
        resp = await client.post(f"/leagues/{league_id}/bets", headers=auth_headers, json={
            "player_id": other_player.id, "prop_market_code": "yellow_card", "stake": 1,
        })
        assert resp.status_code == 400

    async def test_bet_on_unknown_market_fails(self, client, db_session, auth_headers, make_player):
        league_id, player = await create_league_with_squad_and_odds(
            client, db_session, auth_headers, make_player
        )
        resp = await client.post(f"/leagues/{league_id}/bets", headers=auth_headers, json={
            "player_id": player.id, "prop_market_code": "nonexistent_market", "stake": 1,
        })
        assert resp.status_code == 404

    async def test_non_member_cannot_bet(self, client, db_session, auth_headers, make_player):
        league_id, player = await create_league_with_squad_and_odds(
            client, db_session, auth_headers, make_player
        )
        from tests.conftest import register_and_login
        outsider_headers, _ = await register_and_login(client)

        resp = await client.post(f"/leagues/{league_id}/bets", headers=outsider_headers, json={
            "player_id": player.id, "prop_market_code": "yellow_card", "stake": 1,
        })
        assert resp.status_code == 403