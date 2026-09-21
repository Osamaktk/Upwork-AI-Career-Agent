from datetime import UTC, datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.portfolio_matcher import FORMULA_VERSION, PortfolioMatcherAgent
from app.models.enums import EvidenceRelationship, VerificationStatus
from app.models.identity import Skill, VerifiedClaim
from app.models.jobs import EvidenceLink
from app.models.portfolio import PortfolioProject, PortfolioSelection
from app.repositories.evidence import EvidenceRepository
from app.repositories.jobs import JobRepository
from app.schemas.evidence import (
    EvidenceGraphRead,
    EvidenceLinkRead,
    PortfolioSelectionRead,
)
from app.services.matching import normalize_capability, related_capabilities


class EvidenceJobNotFoundError(Exception):
    pass


class EvidenceNotReadyError(Exception):
    pass


class PortfolioSelectionService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.jobs = JobRepository(session)
        self.evidence = EvidenceRepository(session)

    async def select(
        self, job_id: str, user_id: str, agent: PortfolioMatcherAgent
    ) -> PortfolioSelectionRead:
        job = await self.jobs.get(job_id)
        if job is None:
            raise EvidenceJobNotFoundError
        if not (job.normalized_data or {}).get("analysis"):
            raise EvidenceNotReadyError("Analyze the job before selecting portfolio evidence")
        projects_result = await self.session.execute(
            select(PortfolioProject).where(
                PortfolioProject.user_id == user_id,
                PortfolioProject.is_active.is_(True),
                PortfolioProject.verification_status == VerificationStatus.VERIFIED.value,
            )
        )
        projects = list(projects_result.scalars())
        project_ids = [project.id for project in projects]
        claims_by_project: dict[str, list[VerifiedClaim]] = {item: [] for item in project_ids}
        if project_ids:
            claims_result = await self.session.execute(
                select(VerifiedClaim).where(
                    VerifiedClaim.user_id == user_id,
                    VerifiedClaim.portfolio_project_id.in_(project_ids),
                    VerifiedClaim.verification_status == VerificationStatus.VERIFIED.value,
                )
            )
            for claim in claims_result.scalars():
                claims_by_project[claim.portfolio_project_id].append(claim)
        ranked = await agent.rank(job, projects, claims_by_project)
        values = {
            "ranked_projects": [item.model_dump(mode="json") for item in ranked],
            "formula_version": FORMULA_VERSION,
            "model_used": agent.model if agent.use_ai else None,
            "analyzed_at": datetime.now(UTC),
        }
        selection = await self.evidence.get_selection(job_id, user_id)
        if selection is None:
            selection = PortfolioSelection(job_id=job_id, user_id=user_id, **values)
            self.session.add(selection)
        else:
            for key, value in values.items():
                setattr(selection, key, value)
        await self.session.commit()
        await self.session.refresh(selection)
        return PortfolioSelectionRead.model_validate(selection)

    async def get(self, job_id: str, user_id: str) -> PortfolioSelectionRead:
        if await self.jobs.get(job_id) is None:
            raise EvidenceJobNotFoundError
        selection = await self.evidence.get_selection(job_id, user_id)
        if selection is None:
            raise EvidenceNotReadyError("Portfolio selection has not been generated")
        return PortfolioSelectionRead.model_validate(selection)


class EvidenceGraphService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.jobs = JobRepository(session)
        self.repository = EvidenceRepository(session)

    async def rebuild(self, job_id: str, user_id: str) -> EvidenceGraphRead:
        job = await self.jobs.get(job_id)
        if job is None:
            raise EvidenceJobNotFoundError
        requirements = await self.repository.list_requirements(job_id)
        if not requirements:
            raise EvidenceNotReadyError("Analyze the job before building its evidence graph")
        skills_result = await self.session.execute(
            select(Skill).where(
                Skill.user_id == user_id,
                Skill.verification_status == VerificationStatus.VERIFIED.value,
            )
        )
        claims_result = await self.session.execute(
            select(VerifiedClaim).where(
                VerifiedClaim.user_id == user_id,
                VerifiedClaim.verification_status == VerificationStatus.VERIFIED.value,
            )
        )
        projects_result = await self.session.execute(
            select(PortfolioProject).where(
                PortfolioProject.user_id == user_id,
                PortfolioProject.is_active.is_(True),
                PortfolioProject.verification_status == VerificationStatus.VERIFIED.value,
            )
        )
        skills = list(skills_result.scalars())
        claims = list(claims_result.scalars())
        projects = {item.id: item for item in projects_result.scalars()}
        await self.session.execute(
            delete(EvidenceLink).where(
                EvidenceLink.job_id == job_id, EvidenceLink.user_id == user_id
            )
        )
        for requirement in requirements:
            for skill in skills:
                relationship = self._relationship(requirement.value, skill.name)
                if relationship is None:
                    continue
                for claim in claims:
                    project = projects.get(claim.portfolio_project_id or "")
                    if not self._claim_supports(skill, claim, project):
                        continue
                    self.session.add(
                        EvidenceLink(
                            user_id=user_id,
                            job_id=job_id,
                            requirement_id=requirement.id,
                            skill_id=skill.id,
                            claim_id=claim.id,
                            portfolio_project_id=project.id if project else None,
                            relationship=relationship.value,
                            explanation=(
                                f"{requirement.value} is supported by verified skill "
                                f"{skill.name} and verified claim: {claim.claim}"
                            ),
                            proposal_ready=True,
                        )
                    )
        await self.session.commit()
        return await self.get(job_id, user_id)

    async def get(self, job_id: str, user_id: str) -> EvidenceGraphRead:
        job = await self.jobs.get(job_id)
        if job is None:
            raise EvidenceJobNotFoundError
        requirements = await self.repository.list_requirements(job_id)
        links = await self.repository.list_links(job_id, user_id)
        skill_ids = {link.skill_id for link in links}
        claim_ids = {link.claim_id for link in links}
        project_ids = {link.portfolio_project_id for link in links if link.portfolio_project_id}
        skills = await self._by_ids(Skill, skill_ids)
        claims = await self._by_ids(VerifiedClaim, claim_ids)
        projects = await self._by_ids(PortfolioProject, project_ids)
        requirement_map = {item.id: item for item in requirements}
        rendered = [
            EvidenceLinkRead(
                id=link.id,
                requirement_id=link.requirement_id,
                requirement=requirement_map[link.requirement_id].value,
                skill_id=link.skill_id,
                skill=skills[link.skill_id].name,
                claim_id=link.claim_id,
                claim=claims[link.claim_id].claim,
                portfolio_project_id=link.portfolio_project_id,
                portfolio_project=(
                    projects[link.portfolio_project_id].title
                    if link.portfolio_project_id
                    else None
                ),
                relationship=link.relationship,
                explanation=link.explanation,
                proposal_ready=link.proposal_ready,
            )
            for link in links
        ]
        supported = {item.requirement_id for item in rendered if item.proposal_ready}
        return EvidenceGraphRead(
            job_id=job.id,
            job_title=job.title,
            links=rendered,
            unsupported_requirements=[
                requirement.value for requirement in requirements if requirement.id not in supported
            ],
            proposal_ready_link_count=sum(item.proposal_ready for item in rendered),
        )

    async def _by_ids(self, model, identifiers: set[str]):
        if not identifiers:
            return {}
        result = await self.session.execute(select(model).where(model.id.in_(identifiers)))
        return {item.id: item for item in result.scalars()}

    @staticmethod
    def _relationship(required: str, skill: str) -> EvidenceRelationship | None:
        if normalize_capability(required) == normalize_capability(skill):
            return EvidenceRelationship.EXACT
        if related_capabilities(required, skill):
            return EvidenceRelationship.RELATED
        return None

    @staticmethod
    def _claim_supports(
        skill: Skill, claim: VerifiedClaim, project: PortfolioProject | None
    ) -> bool:
        normalized_skill = normalize_capability(skill.name)
        normalized_claim = normalize_capability(claim.claim)
        if f" {normalized_skill} " in f" {normalized_claim} ":
            return True
        if project:
            return any(
                normalize_capability(item) == normalized_skill
                or related_capabilities(item, skill.name)
                for item in [*project.technologies, *project.skills]
            )
        return False
