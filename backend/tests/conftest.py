import os
import uuid
from datetime import datetime, timedelta, timezone

import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.main import app
from app.db import Base, get_db
from app.models.reference import GameWeek, PropMarket
from app.models.player import Player


TEST_DB_PATH = "./test_prop_league.db"
TEST_DATABASE_URL = f"sqlite+aiosqlite:///{TEST_DB_PATH}"

engine = create_async_engine(TEST_DATABASE_URL)
TestSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def cleanup_db_file():
    """Only responsibility: remove the test DB file once, after the
    whole run finishes. No schema setup here — db_session does that
    fresh for every test."""
    yield
    await engine.dispose()
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)


@pytest_asyncio.fixture
async def db_session():
    """
    Full schema reset before every single test: drop everything, recreate
    everything, seed the (genuinely static) reference data, hand out a
    session bound to that fresh schema.

    This trades a little speed for total certainty: there is no shared
    transaction, savepoint, or connection state between tests to get
    subtly wrong — each test starts from a database that provably has
    nothing in it but what this fixture just put there.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    session = TestSessionLocal()

    session.add_all([
        PropMarket(code="yellow_card", display_name="Yellow card"),
        PropMarket(code="anytime_scorer", display_name="Anytime goalscorer"),
    ])
    await session.commit()

    async def _override_get_db():
        yield session

    app.dependency_overrides[get_db] = _override_get_db

    try:
        yield session
    finally:
        await session.close()
        app.dependency_overrides.pop(get_db, None)


@pytest_asyncio.fixture
async def current_gameweek(db_session):
    """A fresh 'current' gameweek for this test only — the schema reset
    in db_session already guarantees no previous test's gameweeks exist."""
    gw = GameWeek(
        fpl_event_id=1,
        deadline_time=datetime.now(timezone.utc) + timedelta(days=3),
        is_current=True,
        is_finished=False,
    )
    db_session.add(gw)
    await db_session.commit()
    await db_session.refresh(gw)
    return gw


@pytest_asyncio.fixture
async def client(db_session, current_gameweek):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


def unique_email() -> str:
    return f"user_{uuid.uuid4().hex[:10]}@example.com"


def unique_username() -> str:
    return f"user_{uuid.uuid4().hex[:10]}"


async def register_and_login(client: AsyncClient, password: str = "testpass123"):
    email = unique_email()
    username = unique_username()

    resp = await client.post("/auth/register", json={
        "email": email, "username": username, "password": password,
    })
    assert resp.status_code == 201, resp.text

    resp = await client.post(
        "/auth/jwt/login",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}, email


@pytest_asyncio.fixture
async def auth_headers(client):
    headers, _ = await register_and_login(client)
    return headers


@pytest_asyncio.fixture
async def make_player(db_session):
    async def _make(position="DEF"):
        player = Player(
            fpl_id=uuid.uuid4().int % 1_000_000,
            name=f"Test Player {uuid.uuid4().hex[:6]}",
            team="Test FC",
            position=position,
        )
        db_session.add(player)
        await db_session.commit()
        await db_session.refresh(player)
        return player
    return _make