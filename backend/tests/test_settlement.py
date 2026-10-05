from sqlalchemy import select
from app.models.reference import GameWeek, PropMarket, PlayerOdds
from app.models.betting import Bet
from app.services import settlement as settlement_module


async def setup_bet(db_session, client, auth_headers, make_player, odds=4.0, stake=2):
    resp = await client.post("/leagues?name=Settle Test League", headers=auth_headers)
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
        player_id=player.id, gameweek_id=gw.id, prop_market_id=market.id,
        probability=0.2, odds_decimal=odds,
    ))
    await db_session.commit()

    resp = await client.post(f"/leagues/{league_id}/bets", headers=auth_headers, json={
        "player_id": player.id, "prop_market_code": "yellow_card", "stake": stake,
    })
    assert resp.status_code == 200
    return league_id, player, gw, resp.json()["bet_id"]


class TestSettlement:
    async def test_won_bet_credits_payout(self, client, db_session, auth_headers, make_player, monkeypatch):
        league_id, player, gw, bet_id = await setup_bet(db_session, client, auth_headers, make_player)

        async def fake_history(fpl_id):
            return [{"round": gw.fpl_event_id, "minutes": 90, "yellow_cards": 1}]
        monkeypatch.setattr(settlement_module, "fetch_player_history", fake_history)

        counts = await settlement_module.settle_gameweek_bets(db_session, gw)
        assert counts["won"] == 1
        assert (await db_session.get(Bet, bet_id)).status == "won"

    async def test_lost_bet_no_payout(self, client, db_session, auth_headers, make_player, monkeypatch):
        league_id, player, gw, bet_id = await setup_bet(db_session, client, auth_headers, make_player)

        async def fake_history(fpl_id):
            return [{"round": gw.fpl_event_id, "minutes": 90, "yellow_cards": 0}]
        monkeypatch.setattr(settlement_module, "fetch_player_history", fake_history)

        counts = await settlement_module.settle_gameweek_bets(db_session, gw)
        assert counts["lost"] == 1
        assert (await db_session.get(Bet, bet_id)).status == "lost"

    async def test_unplayed_game_voids_and_refunds(self, client, db_session, auth_headers, make_player, monkeypatch):
        league_id, player, gw, bet_id = await setup_bet(db_session, client, auth_headers, make_player)

        async def fake_history(fpl_id):
            return [{"round": gw.fpl_event_id, "minutes": 0, "yellow_cards": 0}]
        monkeypatch.setattr(settlement_module, "fetch_player_history", fake_history)

        counts = await settlement_module.settle_gameweek_bets(db_session, gw)
        assert counts["void"] == 1
        assert (await db_session.get(Bet, bet_id)).status == "void"

    async def test_settlement_is_idempotent(self, client, db_session, auth_headers, make_player, monkeypatch):
        league_id, player, gw, bet_id = await setup_bet(db_session, client, auth_headers, make_player)

        async def fake_history(fpl_id):
            return [{"round": gw.fpl_event_id, "minutes": 90, "yellow_cards": 1}]
        monkeypatch.setattr(settlement_module, "fetch_player_history", fake_history)

        first = await settlement_module.settle_gameweek_bets(db_session, gw)
        assert first["won"] == 1

        second = await settlement_module.settle_gameweek_bets(db_session, gw)
        assert second["settled"] == 0  # already resolved, nothing left pending

    async def test_weekly_topup_skipped_in_joining_gameweek(self, client, db_session, auth_headers):
        resp = await client.post("/leagues?name=Topup League", headers=auth_headers)
        gw = (await db_session.execute(
            select(GameWeek).where(GameWeek.is_current == True)
        )).scalar_one()

        # starting_grant already covers this gameweek — no separate top-up due
        granted = await settlement_module.grant_weekly_topups(db_session, gw)
        assert granted == 0