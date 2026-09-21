import pytest

from app.api.dependencies import get_ai_provider
from app.main import app
from app.schemas.matching import (
    MatchNarrative,
    RelationshipKind,
    SemanticRelationship,
    SemanticRelationshipResult,
)
from tests.helpers import create_analyzed_job, create_verified_claim


@pytest.mark.asyncio
async def test_exact_and_missing_skill_match(api_client, auth_headers):
    await create_verified_claim(api_client, auth_headers, "Python")
    job_id = await create_analyzed_job(
        api_client, auth_headers, "match-exact", ["Python", "Kubernetes"]
    )
    response = await api_client.post(f"/api/v1/jobs/{job_id}/match", headers=auth_headers)
    assert response.status_code == 200, response.text
    assert response.json()["exact_matches"] == ["Python"]
    assert response.json()["missing_skills"] == ["Kubernetes"]
    assert response.json()["compatibility_score"] == "37.50"


@pytest.mark.asyncio
async def test_related_skill_match_is_deterministic(api_client, auth_headers):
    await create_verified_claim(api_client, auth_headers, "Computer Vision")
    job_id = await create_analyzed_job(api_client, auth_headers, "match-related", ["OpenCV"])
    response = await api_client.post(f"/api/v1/jobs/{job_id}/match", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["related_matches"] == [
        {"required_skill": "OpenCV", "evidence": "Computer Vision"}
    ]
    assert response.json()["compatibility_score"] == "45.00"


@pytest.mark.asyncio
async def test_no_relevant_or_unverified_skill_scores_zero(api_client, auth_headers):
    unverified = await api_client.post(
        "/api/v1/claims",
        headers=auth_headers,
        json={"claim": "Python", "category": "SKILL", "source": "unverified draft"},
    )
    assert unverified.status_code == 201
    job_id = await create_analyzed_job(api_client, auth_headers, "match-zero", ["Python"])
    response = await api_client.post(f"/api/v1/jobs/{job_id}/match", headers=auth_headers)
    assert response.json()["exact_matches"] == []
    assert response.json()["missing_skills"] == ["Python"]
    assert response.json()["compatibility_score"] == "0.00"


@pytest.mark.asyncio
async def test_verified_portfolio_project_matches(api_client, auth_headers):
    claim = await create_verified_claim(
        api_client, auth_headers, "Built an API project.", "PROJECT"
    )
    project = await api_client.post(
        "/api/v1/portfolio",
        headers=auth_headers,
        json={
            "title": "Verified API",
            "description": "Verified project.",
            "technologies": ["FastAPI"],
            "skills": ["API Development"],
            "verified_claim_ids": [claim["id"]],
        },
    )
    job_id = await create_analyzed_job(api_client, auth_headers, "match-project", ["FastAPI"])
    response = await api_client.post(f"/api/v1/jobs/{job_id}/match", headers=auth_headers)
    assert response.json()["portfolio_project_ids"] == [project.json()["id"]]
    assert response.json()["compatibility_score"] == "15.00"


class UnknownRelationshipProvider:
    async def complete_structured(self, *, prompt, response_model, model):
        if response_model is SemanticRelationshipResult:
            return SemanticRelationshipResult(
                relationships=[
                    SemanticRelationship(
                        required_skill="Rust",
                        capability=None,
                        relationship=RelationshipKind.UNKNOWN,
                        reason="No verified relationship",
                    )
                ]
            )
        return MatchNarrative(
            explanation="Rust remains unsupported by the verified evidence.",
            concerns=["Rust is unknown."],
            supporting_claim_ids=[],
        )


@pytest.mark.asyncio
async def test_ai_unknown_requirement_never_becomes_a_match(api_client, auth_headers):
    await create_verified_claim(api_client, auth_headers, "Python")
    job_id = await create_analyzed_job(api_client, auth_headers, "match-unknown", ["Rust"])
    app.dependency_overrides[get_ai_provider] = lambda: UnknownRelationshipProvider()
    response = await api_client.post(
        f"/api/v1/jobs/{job_id}/match?use_ai=true", headers=auth_headers
    )
    assert response.status_code == 200, response.text
    assert response.json()["related_matches"] == []
    assert response.json()["missing_skills"] == ["Rust"]
    assert response.json()["compatibility_score"] == "0.00"


class HallucinatingProvider:
    async def complete_structured(self, *, prompt, response_model, model):
        return MatchNarrative(
            explanation="The user has an unsupported certification.",
            concerns=[],
            supporting_claim_ids=["invented-claim-id"],
        )


@pytest.mark.asyncio
async def test_hallucinated_claim_id_is_rejected(api_client, auth_headers):
    await create_verified_claim(api_client, auth_headers, "Python")
    job_id = await create_analyzed_job(api_client, auth_headers, "match-hallucination", ["Python"])
    app.dependency_overrides[get_ai_provider] = lambda: HallucinatingProvider()
    response = await api_client.post(
        f"/api/v1/jobs/{job_id}/match?use_ai=true", headers=auth_headers
    )
    assert response.status_code == 422
    assert "unsupported claims" in response.json()["detail"]


class MalformedProvider:
    async def complete_structured(self, *, prompt, response_model, model):
        return {"not": "a validated model"}


@pytest.mark.asyncio
async def test_malformed_ai_analysis_is_rejected(api_client, auth_headers):
    created = await api_client.post(
        "/api/v1/jobs",
        headers=auth_headers,
        json={
            "source_job_id": "malformed-ai",
            "title": "AI analysis",
            "description": "Analyze this job.",
            "required_skills": ["Python"],
        },
    )
    app.dependency_overrides[get_ai_provider] = lambda: MalformedProvider()
    response = await api_client.post(
        f"/api/v1/jobs/{created.json()['id']}/analyze?use_ai=true",
        headers=auth_headers,
    )
    assert response.status_code == 422
