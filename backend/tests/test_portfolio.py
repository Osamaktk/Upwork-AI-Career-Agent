import pytest

from tests.helpers import create_verified_claim


@pytest.mark.asyncio
async def test_portfolio_crud_with_verified_claim(api_client, auth_headers):
    claim = await create_verified_claim(
        api_client, auth_headers, "Built a Python API.", "PROJECT"
    )
    created = await api_client.post(
        "/api/v1/portfolio",
        headers=auth_headers,
        json={
            "title": "API Project",
            "description": "A tested API.",
            "technologies": ["Python", "FastAPI"],
            "skills": ["API Development"],
            "assets": [{"name": "screenshot.png", "kind": "image"}],
            "tags": ["backend"],
            "verified_claim_ids": [claim["id"]],
        },
    )
    assert created.status_code == 201, created.text
    project_id = created.json()["id"]
    assert created.json()["verification_status"] == "VERIFIED"
    assert created.json()["verified_claim_ids"] == [claim["id"]]

    listed = await api_client.get("/api/v1/portfolio", headers=auth_headers)
    assert len(listed.json()) == 1
    detail = await api_client.get(f"/api/v1/portfolio/{project_id}", headers=auth_headers)
    assert detail.status_code == 200

    updated = await api_client.patch(
        f"/api/v1/portfolio/{project_id}",
        headers=auth_headers,
        json={"result": "A verified test result."},
    )
    assert updated.status_code == 200
    assert updated.json()["result"] == "A verified test result."

    deleted = await api_client.delete(
        f"/api/v1/portfolio/{project_id}", headers=auth_headers
    )
    assert deleted.status_code == 204
    assert (await api_client.get("/api/v1/portfolio", headers=auth_headers)).json() == []


@pytest.mark.asyncio
async def test_portfolio_rejects_unverified_claim(api_client, auth_headers):
    claim = await api_client.post(
        "/api/v1/claims",
        headers=auth_headers,
        json={"claim": "Maybe built it", "category": "PROJECT", "source": "draft"},
    )
    response = await api_client.post(
        "/api/v1/portfolio",
        headers=auth_headers,
        json={
            "title": "Unsupported project",
            "description": "Should fail.",
            "verified_claim_ids": [claim.json()["id"]],
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_portfolio_validation_requires_title_and_description(api_client, auth_headers):
    response = await api_client.post(
        "/api/v1/portfolio",
        headers=auth_headers,
        json={"title": "", "description": ""},
    )
    assert response.status_code == 422
