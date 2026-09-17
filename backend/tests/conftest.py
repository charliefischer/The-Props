import os
import uuid
from datetime import datetime, timedelta, timezone

import pytest
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
TestSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def override_get_db():
    async with TestSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_db():
    """Fresh schema once per test run, real file cleaned up afterwards."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def seed_reference_data(setup_db):
    """Prop markets and a currently-open gameweek, shared by every test."""
    async with TestSessionLocal() as session:
        session.add_all([
            PropMarket(code="yellow_card", display_name="Yellow card"),
            PropMarket(code="anytime_scorer", display_name="Anytime goalscorer"),
        ])
        session.add(GameWeek(
            fpl_event_id=1,
            deadline_time=datetime.now(timezone.utc) + timedelta(days=3),
            is_current=True,
            is_finished=False,
        ))
        await session.commit()


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def db_session():
    async with TestSessionLocal() as session:
        yield session


def unique_email() -> str:
    return f"user_{uuid.uuid4().hex[:10]}@example.com"


def unique_username() -> str:
    return f"user_{uuid.uuid4().hex[:10]}"


async def register_and_login(client: AsyncClient, password: str = "testpass123"):
    """Registers a fresh, uniquely-named user and returns (auth_headers, email)."""
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
    """Factory fixture: create a fresh test player on demand."""
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