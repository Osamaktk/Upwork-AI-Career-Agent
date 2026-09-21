import pytest


@pytest.mark.asyncio
async def test_development_seed_is_synthetic_and_idempotent(api_client, auth_headers):
    first = await api_client.post("/api/v1/development/seed", headers=auth_headers)
    assert first.status_code == 200, first.text
    assert first.json()["synthetic"] is True
    assert first.json()["profile_created"] is True
    assert first.json()["claims_created"] >= 5
    assert first.json()["projects_created"] == 3

    second = await api_client.post("/api/v1/development/seed", headers=auth_headers)
    assert second.status_code == 200
    assert second.json()["profile_created"] is False
    assert second.json()["claims_created"] == 0
    assert second.json()["projects_created"] == 0


@pytest.mark.asyncio
async def test_batch_analysis_ranks_persisted_matches_and_dashboard(api_client, auth_headers):
    seeded = await api_client.post("/api/v1/development/seed", headers=auth_headers)
    imported = await api_client.post("/api/v1/jobs/import/sample", headers=auth_headers)
    assert seeded.status_code == 200
    assert imported.status_code == 200

    batch = await api_client.post("/api/v1/jobs/analyze/batch", headers=auth_headers)
    assert batch.status_code == 200, batch.text
    assert batch.json()["analyzed_count"] == 3
    assert batch.json()["matched_count"] == 3
    assert batch.json()["failed_count"] == 0
    scores = [float(item["compatibility_score"]) for item in batch.json()["ranked_matches"]]
    assert scores == sorted(scores, reverse=True)

    dashboard = await api_client.get("/api/v1/dashboard/summary", headers=auth_headers)
    assert dashboard.status_code == 200
    assert dashboard.json()["total_jobs"] == 3
    assert dashboard.json()["analyzed_jobs"] == 3
    assert dashboard.json()["matched_jobs"] == 3
    assert dashboard.json()["portfolio_count"] == 3
