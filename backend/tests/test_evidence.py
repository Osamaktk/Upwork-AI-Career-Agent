import pytest

from app.api.dependencies import get_ai_provider
from app.main import app
from app.schemas.evidence import (
    PortfolioNarrative,
    PortfolioNarrativeResult,
)
from tests.helpers import create_analyzed_job


async def seed_development_data(api_client, auth_headers):
    response = await api_client.post("/api/v1/development/seed", headers=auth_headers)
    assert response.status_code == 200, response.text


@pytest.mark.asyncio
async def test_portfolio_selection_is_ranked_explained_and_persisted(api_client, auth_headers):
    await seed_development_data(api_client, auth_headers)
    job_id = await create_analyzed_job(
        api_client, auth_headers, "portfolio-selection", ["OpenCV", "Python"]
    )
    first = await api_client.post(
        f"/api/v1/jobs/{job_id}/portfolio-selection", headers=auth_headers
    )
    assert first.status_code == 200, first.text
    ranked = first.json()["ranked_projects"]
    assert ranked
    assert ranked[0]["title"] == "Synthetic Facial Recognition Attendance System"
    assert ranked[0]["verified_claim_ids"]
    assert ranked[0]["explanation"]
    assert ranked == sorted(
        ranked, key=lambda item: (-float(item["relevance_score"]), item["title"].casefold())
    )

    repeated = await api_client.post(
        f"/api/v1/jobs/{job_id}/portfolio-selection", headers=auth_headers
    )
    assert repeated.json()["id"] == first.json()["id"]


class HallucinatingPortfolioProvider:
    async def complete_structured(self, *, prompt, response_model, model):
        return PortfolioNarrativeResult(
            projects=[
                PortfolioNarrative(
                    project_id="invented-project",
                    explanation="Unsupported project.",
                    supporting_claim_ids=["invented-claim"],
                )
            ]
        )


@pytest.mark.asyncio
async def test_portfolio_ai_cannot_add_projects_or_claims(api_client, auth_headers):
    await seed_development_data(api_client, auth_headers)
    job_id = await create_analyzed_job(
        api_client, auth_headers, "portfolio-hallucination", ["FastAPI"]
    )
    app.dependency_overrides[get_ai_provider] = lambda: HallucinatingPortfolioProvider()
    response = await api_client.post(
        f"/api/v1/jobs/{job_id}/portfolio-selection?use_ai=true",
        headers=auth_headers,
    )
    assert response.status_code == 422
    assert "unsupported project" in response.json()["detail"]


@pytest.mark.asyncio
async def test_evidence_graph_traces_only_verified_proposal_ready_data(api_client, auth_headers):
    await seed_development_data(api_client, auth_headers)
    unverified = await api_client.post(
        "/api/v1/claims",
        headers=auth_headers,
        json={
            "claim": "Unverified OpenCV production experience.",
            "category": "PROJECT",
            "source": "unverified test input",
        },
    )
    job_id = await create_analyzed_job(
        api_client, auth_headers, "evidence-graph", ["OpenCV", "Kubernetes"]
    )
    response = await api_client.post(
        f"/api/v1/jobs/{job_id}/evidence/rebuild", headers=auth_headers
    )
    assert response.status_code == 200, response.text
    graph = response.json()
    assert graph["links"]
    assert "Kubernetes" in graph["unsupported_requirements"]
    assert all(item["proposal_ready"] for item in graph["links"])
    assert all(item["claim_id"] != unverified.json()["id"] for item in graph["links"])
    assert any(item["portfolio_project_id"] for item in graph["links"])
    assert all(
        item["requirement_id"] and item["skill_id"] and item["claim_id"]
        for item in graph["links"]
    )


@pytest.mark.asyncio
async def test_phase3_evaluation_dataset_passes(api_client, auth_headers):
    response = await api_client.get("/api/v1/evaluations/phase3", headers=auth_headers)
    assert response.status_code == 200, response.text
    metrics = response.json()
    assert metrics["case_count"] == 5
    assert metrics["skill_extraction_accuracy"] == "100.00"
    assert metrics["portfolio_selection_accuracy"] == "100.00"
    assert metrics["unsupported_claim_rate"] == "0.00"
    assert metrics["false_match_rate"] == "0.00"
    assert metrics["passed"] is True
