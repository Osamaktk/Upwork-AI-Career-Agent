import json

import pytest

from app.services.jobs import JobService


@pytest.mark.asyncio
async def test_sample_import_is_validated_and_idempotent(api_client, auth_headers):
    first = await api_client.post("/api/v1/jobs/import/sample", headers=auth_headers)
    assert first.status_code == 200, first.text
    assert first.json() == {
        "imported_count": 3,
        "skipped_count": 0,
        "duplicate_count": 0,
        "validation_errors": [],
    }

    second = await api_client.post("/api/v1/jobs/import/sample", headers=auth_headers)
    assert second.status_code == 200
    assert second.json()["imported_count"] == 0
    assert second.json()["skipped_count"] == 3
    assert second.json()["duplicate_count"] == 3


@pytest.mark.asyncio
async def test_invalid_fixture_returns_useful_error(test_session_factory, tmp_path):
    (tmp_path / "job_invalid.json").write_text(
        json.dumps({"source": "sample", "source_job_id": "broken"}), encoding="utf-8"
    )
    async with test_session_factory() as session:
        result = await JobService(session).import_samples(tmp_path)
    assert result.imported_count == 0
    assert result.skipped_count == 1
    assert result.validation_errors[0].file == "job_invalid.json"
    assert "title" in result.validation_errors[0].message


@pytest.mark.asyncio
async def test_jobs_support_pagination_filtering_detail_and_update(api_client, auth_headers):
    await api_client.post("/api/v1/jobs/import/sample", headers=auth_headers)
    page = await api_client.get(
        "/api/v1/jobs?page=1&page_size=1&skill=Python&source=sample",
        headers=auth_headers,
    )
    assert page.status_code == 200
    assert page.json()["page_size"] == 1
    assert page.json()["total"] >= 1
    job_id = page.json()["items"][0]["id"]

    detail = await api_client.get(f"/api/v1/jobs/{job_id}", headers=auth_headers)
    assert detail.status_code == 200
    assert detail.json()["analysis"] is None

    updated = await api_client.patch(
        f"/api/v1/jobs/{job_id}",
        headers=auth_headers,
        json={"status": "ACTIVE", "budget_max": 3000},
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "ACTIVE"


@pytest.mark.asyncio
async def test_manual_job_validation_and_duplicate_detection(api_client, auth_headers):
    invalid = await api_client.post(
        "/api/v1/jobs",
        headers=auth_headers,
        json={
            "source_job_id": "manual-1",
            "title": "Invalid budget",
            "description": "Budget bounds are reversed.",
            "budget_min": 500,
            "budget_max": 100,
        },
    )
    assert invalid.status_code == 422

    payload = {
        "source_job_id": "manual-2",
        "title": "Valid job",
        "description": "Build a Python API.",
        "required_skills": ["Python"],
    }
    first = await api_client.post("/api/v1/jobs", headers=auth_headers, json=payload)
    duplicate = await api_client.post("/api/v1/jobs", headers=auth_headers, json=payload)
    assert first.status_code == 201
    assert duplicate.status_code == 409


@pytest.mark.asyncio
async def test_job_analysis_is_structured_and_persisted(api_client, auth_headers):
    created = await api_client.post(
        "/api/v1/jobs",
        headers=auth_headers,
        json={
            "source_job_id": "analysis-1",
            "title": "FastAPI service",
            "description": "Build a production API and include retries and audit events.",
            "required_skills": ["Python", "FastAPI"],
        },
    )
    job_id = created.json()["id"]
    analysis = await api_client.post(f"/api/v1/jobs/{job_id}/analyze", headers=auth_headers)
    assert analysis.status_code == 200
    assert analysis.json()["required_skills"] == ["Python", "FastAPI"]
    assert "production" in analysis.json()["complexity_indicators"]

    detail = await api_client.get(f"/api/v1/jobs/{job_id}", headers=auth_headers)
    assert detail.json()["analysis_state"] == "ANALYZED"
    assert detail.json()["analysis"]["required_skills"] == ["Python", "FastAPI"]
