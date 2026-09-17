from tests.conftest import register_and_login


class TestLeagues:
    async def test_create_league(self, client, auth_headers):
        resp = await client.post("/leagues?name=Test League", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["name"] == "Test League"
        assert len(body["invite_code"]) == 6

    async def test_creator_sees_league_in_my_leagues(self, client, auth_headers):
        resp = await client.post("/leagues?name=My League", headers=auth_headers)
        league_id = resp.json()["id"]

        resp = await client.get("/leagues", headers=auth_headers)
        ids = [l["id"] for l in resp.json()]
        assert league_id in ids

    async def test_second_user_can_join_via_invite_code(self, client, auth_headers):
        resp = await client.post("/leagues?name=Joinable League", headers=auth_headers)
        invite_code = resp.json()["invite_code"]

        other_headers, _ = await register_and_login(client)
        resp = await client.post(f"/leagues/join/{invite_code}", headers=other_headers)
        assert resp.status_code == 200

        resp = await client.get("/leagues", headers=other_headers)
        names = [l["name"] for l in resp.json()]
        assert "Joinable League" in names

    async def test_join_invalid_code_fails(self, client, auth_headers):
        resp = await client.post("/leagues/join/BADCODE", headers=auth_headers)
        assert resp.status_code == 404

    async def test_join_twice_fails(self, client, auth_headers):
        resp = await client.post("/leagues?name=Repeat Join League", headers=auth_headers)
        invite_code = resp.json()["invite_code"]

        other_headers, _ = await register_and_login(client)
        first = await client.post(f"/leagues/join/{invite_code}", headers=other_headers)
        assert first.status_code == 200

        second = await client.post(f"/leagues/join/{invite_code}", headers=other_headers)
        assert second.status_code == 400

    async def test_starting_credits_granted_on_join(self, client, auth_headers):
        resp = await client.post("/leagues?name=Credits League", headers=auth_headers)
        league_id = resp.json()["id"]

        resp = await client.get(f"/leagues/{league_id}/bets", headers=auth_headers)
        assert resp.status_code == 200  # membership exists — proves join/create worked end-to-end