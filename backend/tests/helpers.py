async def create_verified_claim(api_client, auth_headers, claim: str, category: str = "SKILL"):
    created = await api_client.post(
        "/api/v1/claims",
        headers=auth_headers,
        json={
            "claim": claim,
            "category": category,
            "source": "test evidence",
            "notes": "verified in test",
        },
    )
    assert created.status_code == 201, created.text
    verified = await api_client.post(
        f"/api/v1/claims/{created.json()['id']}/verify", headers=auth_headers
    )
    assert verified.status_code == 200, verified.text
    return verified.json()


async def create_analyzed_job(api_client, auth_headers, source_job_id: str, skills: list[str]):
    created = await api_client.post(
        "/api/v1/jobs",
        headers=auth_headers,
        json={
            "source": "manual",
            "source_job_id": source_job_id,
            "title": f"Test job {source_job_id}",
            "description": "Build and test the requested capability.",
            "budget_type": "fixed",
            "budget_min": 100,
            "budget_max": 200,
            "required_skills": skills,
        },
    )
    assert created.status_code == 201, created.text
    job_id = created.json()["id"]
    analyzed = await api_client.post(f"/api/v1/jobs/{job_id}/analyze", headers=auth_headers)
    assert analyzed.status_code == 200, analyzed.text
    return job_id
