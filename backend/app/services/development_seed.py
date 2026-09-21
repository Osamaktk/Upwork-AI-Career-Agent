import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.models.enums import ReviewStatus
from app.models.identity import Skill, VerifiedClaim
from app.models.portfolio import PortfolioProject
from app.models.system import AuditLog
from app.repositories.claims import ClaimRepository
from app.repositories.portfolio import PortfolioRepository
from app.repositories.profiles import ProfileRepository
from app.schemas.development import DevelopmentSeedResult
from app.schemas.profile import ProfileCreate
from app.services.profiles import ProfileService


class DevelopmentSeedDisabledError(Exception):
    pass


class InvalidDevelopmentSeedError(Exception):
    pass


class DevelopmentSeedService:
    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self.session = session
        self.settings = settings

    async def seed(self, user_id: str, path: Path) -> DevelopmentSeedResult:
        if self.settings.app_env == "production":
            raise DevelopmentSeedDisabledError
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("synthetic") is not True:
            raise InvalidDevelopmentSeedError("Development seed must be marked synthetic")

        profile_created = False
        profile_repository = ProfileRepository(self.session)
        if await profile_repository.get_for_user(user_id) is None:
            await ProfileService(self.session).create(
                user_id, ProfileCreate.model_validate(data.get("profile", {}))
            )
            profile_created = True

        skill_result = await self.session.execute(select(Skill).where(Skill.user_id == user_id))
        existing_skills = {
            (skill.name.casefold(), skill.category): skill for skill in skill_result.scalars()
        }
        skills_created = 0
        for item in data.get("skills", []):
            identity = (item["name"].casefold(), item["category"])
            if identity in existing_skills:
                existing_skills[identity].verification_status = item["verification_status"]
                continue
            skill = Skill(user_id=user_id, **item)
            self.session.add(skill)
            existing_skills[identity] = skill
            skills_created += 1

        existing_claims = await ClaimRepository(self.session).list_for_user(user_id)
        claim_by_text = {claim.claim: claim for claim in existing_claims}
        claims_created = 0
        for item in data.get("claims", []):
            if item["claim"] in claim_by_text:
                continue
            claim = VerifiedClaim(user_id=user_id, **item)
            self.session.add(claim)
            await self.session.flush()
            claim_by_text[claim.claim] = claim
            claims_created += 1

        project_repository = PortfolioRepository(self.session)
        existing_projects = {
            project.title for project in await project_repository.list_for_user(user_id)
        }
        projects_created = 0
        for item in data.get("projects", []):
            if item["title"] in existing_projects:
                continue
            claim_texts = item.pop("verified_claim_texts", [])
            project = PortfolioProject(user_id=user_id, **item)
            self.session.add(project)
            await self.session.flush()
            for text in claim_texts:
                claim = claim_by_text.get(text)
                if claim is None or claim.verification_status != "VERIFIED":
                    raise InvalidDevelopmentSeedError(
                        f"Project references a missing verified claim: {text}"
                    )
                claim.portfolio_project_id = project.id
            existing_projects.add(project.title)
            projects_created += 1

        self.session.add(
            AuditLog(
                user_id=user_id,
                action="development.seed_applied",
                input_reference=str(path),
                output={
                    "synthetic": True,
                    "skills_created": skills_created,
                    "claims_created": claims_created,
                    "projects_created": projects_created,
                },
                approval_status=ReviewStatus.APPROVED.value,
                result="success",
            )
        )
        await self.session.commit()
        return DevelopmentSeedResult(
            profile_created=profile_created,
            skills_created=skills_created,
            claims_created=claims_created,
            projects_created=projects_created,
        )
