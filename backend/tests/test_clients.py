import pytest

from app.agents.client_analyzer import ClientAnalysisDraft
from app.api.dependencies import get_ai_provider
from app.main import app
from app.schemas.clients import AnalysisStatement


async def import_sample_context(api_client, auth_headers):
    imported = await api_client.post("/api/v1/jobs/import/sample", headers=auth_headers)
    assert imported.status_code == 200, imported.text
    clients = await api_client.get("/api/v1/clients", headers=auth_headers)
    jobs = await api_client.get("/api/v1/jobs?page_size=100", headers=auth_headers)
    assert clients.status_code == 200
    client_by_id = {item["id"]: item for item in clients.json()}
    job = next(item for item in jobs.json()["items"] if item["client_id"] in client_by_id)
    return client_by_id[job["client_id"]], job


@pytest.mark.asyncio
async def test_sample_client_facts_retain_sources_and_classification(api_client, auth_headers):
    client, _ = await import_sample_context(api_client, auth_headers)
    detail = await api_client.get(f"/api/v1/clients/{client['id']}", headers=auth_headers)
    assert detail.status_code == 200, detail.text
    facts = detail.json()["facts"]
    assert {item["classification"] for item in facts} >= {"FACT", "UNKNOWN"}
    sourced_fact = next(item for item in facts if item["classification"] == "FACT")
    assert sourced_fact["verification_status"] == "VERIFIED"
    assert sourced_fact["client_source_id"]
    assert sourced_fact["source_type"]
    assert sourced_fact["source_url"]

    repeated = await api_client.post("/api/v1/jobs/import/sample", headers=auth_headers)
    assert repeated.status_code == 200
    facts_after = await api_client.get(
        f"/api/v1/clients/{client['id']}/facts", headers=auth_headers
    )
    assert len(facts_after.json()) == len(facts)


@pytest.mark.asyncio
async def test_client_fact_state_validation(api_client, auth_headers):
    created = await api_client.post(
        "/api/v1/clients",
        headers=auth_headers,
        json={"source": "manual", "source_client_id": "client-validation"},
    )
    client_id = created.json()["id"]
    missing_source = await api_client.post(
        f"/api/v1/clients/{client_id}/facts",
        headers=auth_headers,
        json={
            "fact": "A fact without evidence.",
            "fact_type": "COMPANY",
            "classification": "FACT",
            "verification_status": "VERIFIED",
        },
    )
    assert missing_source.status_code == 422

    verified_inference = await api_client.post(
        f"/api/v1/clients/{client_id}/facts",
        headers=auth_headers,
        json={
            "fact": "An interpretation.",
            "fact_type": "GOAL",
            "classification": "INFERENCE",
            "verification_status": "VERIFIED",
        },
    )
    assert verified_inference.status_code == 422

    source = await api_client.post(
        f"/api/v1/clients/{client_id}/sources",
        headers=auth_headers,
        json={"source_type": "public_company_page", "url": "https://example.com/about"},
    )
    fact = await api_client.post(
        f"/api/v1/clients/{client_id}/facts",
        headers=auth_headers,
        json={
            "client_source_id": source.json()["id"],
            "fact": "The supplied company page names Example Company.",
            "fact_type": "COMPANY",
            "classification": "FACT",
            "verification_status": "VERIFIED",
        },
    )
    assert fact.status_code == 201
    assert fact.json()["source_url"] == "https://example.com/about"

    updated = await api_client.patch(
        f"/api/v1/clients/{client_id}",
        headers=auth_headers,
        json={"company": "Example Company"},
    )
    assert updated.status_code == 200
    assert updated.json()["company"] == "Example Company"


@pytest.mark.asyncio
async def test_structured_client_analysis_separates_facts_and_unknowns(api_client, auth_headers):
    client, job = await import_sample_context(api_client, auth_headers)
    analyzed_job = await api_client.post(
        f"/api/v1/jobs/{job['id']}/analyze", headers=auth_headers
    )
    assert analyzed_job.status_code == 200
    response = await api_client.post(
        f"/api/v1/clients/{client['id']}/analyze?job_id={job['id']}",
        headers=auth_headers,
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["verified_facts"]
    assert payload["unknowns"]
    assert payload["requirements"] == job["required_skills"]
    assert "rating" not in payload
    assert "good_client" not in payload


class UnsupportedClientFactProvider:
    async def complete_structured(self, *, prompt, response_model, model):
        return ClientAnalysisDraft(
            inferences=[
                AnalysisStatement(
                    text="Unsupported company inference.",
                    supporting_fact_ids=["invented-fact-id"],
                )
            ]
        )


@pytest.mark.asyncio
async def test_client_analysis_rejects_hallucinated_evidence(api_client, auth_headers):
    client, job = await import_sample_context(api_client, auth_headers)
    app.dependency_overrides[get_ai_provider] = lambda: UnsupportedClientFactProvider()
    response = await api_client.post(
        f"/api/v1/clients/{client['id']}/analyze?job_id={job['id']}&use_ai=true",
        headers=auth_headers,
    )
    assert response.status_code == 422
    assert "unsupported facts" in response.json()["detail"]
