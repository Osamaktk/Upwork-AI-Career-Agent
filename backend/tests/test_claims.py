import pytest
from sqlalchemy import select

from app.models.system import AuditLog


@pytest.mark.asyncio
async def test_claim_lifecycle_creates_audit_records(
    api_client, auth_headers, test_session_factory
):
    created = await api_client.post(
        "/api/v1/claims",
        headers=auth_headers,
        json={
            "claim": "Python",
            "category": "SKILL",
            "source": "certificate.pdf",
            "notes": "Reviewed manually",
        },
    )
    assert created.status_code == 201
    claim_id = created.json()["id"]
    assert created.json()["verification_status"] == "UNVERIFIED"

    for action, expected in (
        ("verify", "VERIFIED"),
        ("unverify", "UNVERIFIED"),
        ("expire", "EXPIRED"),
    ):
        response = await api_client.post(
            f"/api/v1/claims/{claim_id}/{action}", headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["verification_status"] == expected

    updated = await api_client.patch(
        f"/api/v1/claims/{claim_id}",
        headers=auth_headers,
        json={"notes": "Updated note"},
    )
    assert updated.status_code == 200
    listed = await api_client.get("/api/v1/claims", headers=auth_headers)
    assert listed.status_code == 200
    assert listed.json()[0]["notes"] == "Updated note"

    async with test_session_factory() as session:
        records = list(
            (
                await session.execute(
                    select(AuditLog).where(
                        AuditLog.action == "claim.verification_status_changed"
                    )
                )
            ).scalars()
        )
    assert [record.output["to"] for record in records] == [
        "VERIFIED",
        "UNVERIFIED",
        "EXPIRED",
    ]


@pytest.mark.asyncio
async def test_claim_cannot_start_verified(api_client, auth_headers):
    response = await api_client.post(
        "/api/v1/claims",
        headers=auth_headers,
        json={
            "claim": "Unsupported claim",
            "category": "EXPERIENCE",
            "source": "none",
            "verification_status": "VERIFIED",
        },
    )
    assert response.status_code == 422
