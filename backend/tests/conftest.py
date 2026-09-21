from collections.abc import AsyncIterator

import httpx
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.db.base import Base
from app.db.session import get_session
from app.main import app


@pytest_asyncio.fixture
async def test_session_factory(tmp_path):
    database_path = tmp_path / "test.db"
    engine = create_async_engine(
        f"sqlite+aiosqlite:///{database_path.as_posix()}", poolclass=NullPool
    )
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    yield factory
    await engine.dispose()


@pytest_asyncio.fixture
async def api_client(test_session_factory) -> AsyncIterator[httpx.AsyncClient]:
    async def override_session():
        async with test_session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def auth_headers(api_client) -> dict[str, str]:
    credentials = {"email": "phase2@example.com", "password": "a-secure-test-password"}
    response = await api_client.post("/api/v1/auth/register", json=credentials)
    assert response.status_code == 201
    login = await api_client.post("/api/v1/auth/login", json=credentials)
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


@pytest.fixture
def sample_jobs_directory():
    from pathlib import Path

    return Path(__file__).resolve().parents[2] / "sample_jobs"
