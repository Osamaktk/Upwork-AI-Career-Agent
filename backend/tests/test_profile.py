import pytest


@pytest.mark.asyncio
async def test_create_update_and_retrieve_profile(api_client, auth_headers):
    created = await api_client.post(
        "/api/v1/profile",
        headers=auth_headers,
        json={
            "title": "AI Developer",
            "overview": "Builds evidence-backed systems.",
            "location": None,
            "years_experience": 2.5,
            "primary_skills": ["Python", "python", "FastAPI"],
            "programming_languages": ["Python"],
        },
    )
    assert created.status_code == 201, created.text
    assert created.json()["primary_skills"] == ["Python", "FastAPI"]
    assert created.json()["location"] is None

    updated = await api_client.patch(
        "/api/v1/profile",
        headers=auth_headers,
        json={"location": "Remote", "frameworks": ["FastAPI", "Flutter"]},
    )
    assert updated.status_code == 200
    assert updated.json()["location"] == "Remote"
    assert updated.json()["title"] == "AI Developer"

    retrieved = await api_client.get("/api/v1/profile", headers=auth_headers)
    assert retrieved.status_code == 200
    assert retrieved.json() == updated.json()


@pytest.mark.asyncio
async def test_profile_validation_rejects_negative_experience(api_client, auth_headers):
    response = await api_client.post(
        "/api/v1/profile",
        headers=auth_headers,
        json={"years_experience": -1},
    )
    assert response.status_code == 422
