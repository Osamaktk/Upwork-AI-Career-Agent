import pytest


@pytest.mark.asyncio
async def test_register_login_and_read_current_user(api_client):
    credentials = {"email": "Owner@Example.com", "password": "a-secure-test-password"}

    register = await api_client.post("/api/v1/auth/register", json=credentials)
    assert register.status_code == 201
    assert register.json()["email"] == "owner@example.com"
    assert "password" not in register.text

    login = await api_client.post("/api/v1/auth/login", json=credentials)
    assert login.status_code == 200
    token = login.json()["access_token"]

    current = await api_client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert current.status_code == 200
    assert current.json()["id"] == register.json()["id"]


@pytest.mark.asyncio
async def test_duplicate_registration_is_rejected(api_client):
    credentials = {"email": "same@example.com", "password": "a-secure-test-password"}

    assert (await api_client.post("/api/v1/auth/register", json=credentials)).status_code == 201
    duplicate = await api_client.post("/api/v1/auth/register", json=credentials)

    assert duplicate.status_code == 409


@pytest.mark.asyncio
async def test_me_requires_a_valid_token(api_client):
    response = await api_client.get("/api/v1/auth/me")
    assert response.status_code == 401
