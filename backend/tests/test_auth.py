from tests.conftest import register_and_login, unique_email, unique_username


class TestAuth:
    async def test_register_creates_user(self, client):
        email = unique_email()
        username = unique_username()
        resp = await client.post("/auth/register", json={
            "email": email, "username": username, "password": "testpass123",
        })
        assert resp.status_code == 201
        assert resp.json()["email"] == email

    async def test_register_duplicate_email_fails(self, client):
        email = unique_email()
        payload = {"email": email, "username": unique_username(), "password": "testpass123"}
        first = await client.post("/auth/register", json=payload)
        assert first.status_code == 201

        second = await client.post("/auth/register", json={
            **payload, "username": unique_username(),  # different username, same email
        })
        assert second.status_code == 400

    async def test_login_wrong_password_fails(self, client):
        headers, email = await register_and_login(client, password="correct-password")
        resp = await client.post(
            "/auth/jwt/login",
            data={"username": email, "password": "wrong-password"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert resp.status_code == 400

    async def test_me_requires_auth(self, client):
        resp = await client.get("/users/me")
        assert resp.status_code == 401

    async def test_me_returns_current_user(self, client):
        headers, email = await register_and_login(client)
        resp = await client.get("/users/me", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["email"] == email