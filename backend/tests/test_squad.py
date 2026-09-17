class TestSquad:
    async def test_empty_squad_by_default(self, client, auth_headers):
        resp = await client.get("/squad", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_add_and_view_player(self, client, auth_headers, make_player):
        player = await make_player()
        resp = await client.post(f"/squad/add/{player.id}", headers=auth_headers)
        assert resp.status_code == 200

        resp = await client.get("/squad", headers=auth_headers)
        ids = [p["id"] for p in resp.json()]
        assert player.id in ids

    async def test_duplicate_add_fails(self, client, auth_headers, make_player):
        player = await make_player()
        await client.post(f"/squad/add/{player.id}", headers=auth_headers)
        resp = await client.post(f"/squad/add/{player.id}", headers=auth_headers)
        assert resp.status_code == 400

    async def test_remove_player(self, client, auth_headers, make_player):
        player = await make_player()
        await client.post(f"/squad/add/{player.id}", headers=auth_headers)

        resp = await client.delete(f"/squad/remove/{player.id}", headers=auth_headers)
        assert resp.status_code == 200

        resp = await client.get("/squad", headers=auth_headers)
        ids = [p["id"] for p in resp.json()]
        assert player.id not in ids

    async def test_remove_player_not_in_squad_fails(self, client, auth_headers, make_player):
        player = await make_player()
        resp = await client.delete(f"/squad/remove/{player.id}", headers=auth_headers)
        assert resp.status_code == 404

    async def test_squad_cap_enforced(self, client, auth_headers, make_player):
        for _ in range(15):
            player = await make_player()
            resp = await client.post(f"/squad/add/{player.id}", headers=auth_headers)
            assert resp.status_code == 200

        sixteenth = await make_player()
        resp = await client.post(f"/squad/add/{sixteenth.id}", headers=auth_headers)
        assert resp.status_code == 400