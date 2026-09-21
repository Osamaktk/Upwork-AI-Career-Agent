import json
from decimal import Decimal

from app.models.identity import VerifiedClaim
from app.models.jobs import Job
from app.models.portfolio import PortfolioProject
from app.schemas.evidence import (
    PortfolioNarrativeResult,
    RankedPortfolioProject,
)
from app.schemas.matching import RelatedMatch
from app.services.ai_provider import AIProvider, DisabledAIProvider, InvalidStructuredOutputError
from app.services.matching import normalize_capability, related_capabilities

FORMULA_VERSION = "portfolio-v1"


class UnsupportedPortfolioEvidenceError(ValueError):
    pass


class PortfolioMatcherAgent:
    def __init__(
        self,
        provider: AIProvider | None = None,
        model: str | None = None,
        use_ai: bool = False,
    ) -> None:
        self.provider = provider or DisabledAIProvider()
        self.model = model
        self.use_ai = use_ai

    async def rank(
        self,
        job: Job,
        projects: list[PortfolioProject],
        claims_by_project: dict[str, list[VerifiedClaim]],
    ) -> list[RankedPortfolioProject]:
        ranked = [
            self._score_project(job, project, claims_by_project.get(project.id, []))
            for project in projects
        ]
        ranked = [item for item in ranked if item.relevance_score > 0]
        ranked.sort(key=lambda item: (-item.relevance_score, item.title.casefold()))
        if self.use_ai and ranked:
            await self._apply_narratives(job, ranked)
        return ranked

    @staticmethod
    def _score_project(
        job: Job, project: PortfolioProject, claims: list[VerifiedClaim]
    ) -> RankedPortfolioProject:
        capabilities = [*project.technologies, *project.skills]
        exact: list[str] = []
        related: list[RelatedMatch] = []
        for requirement in job.required_skills:
            direct = next(
                (
                    item
                    for item in capabilities
                    if normalize_capability(item) == normalize_capability(requirement)
                ),
                None,
            )
            if direct:
                exact.append(requirement)
                continue
            related_capability = next(
                (item for item in capabilities if related_capabilities(requirement, item)),
                None,
            )
            if related_capability:
                related.append(
                    RelatedMatch(required_skill=requirement, evidence=related_capability)
                )
        skill_score = Decimal("0")
        if job.required_skills:
            weighted = Decimal(len(exact)) + Decimal("0.6") * Decimal(len(related))
            skill_score = Decimal("70") * weighted / Decimal(len(job.required_skills))
        evidence_score = Decimal("30") if claims and (exact or related) else Decimal("0")
        score = min(Decimal("100"), skill_score + evidence_score).quantize(Decimal("0.01"))
        overlap = [*exact, *(item.required_skill for item in related)]
        explanation = (
            f"{project.title} overlaps {', '.join(overlap)} and has verified claim support."
            if overlap and claims
            else f"{project.title} overlaps {', '.join(overlap)} but lacks verified claim support."
            if overlap
            else f"{project.title} has verified evidence but no requirement overlap."
        )
        return RankedPortfolioProject(
            project_id=project.id,
            title=project.title,
            relevance_score=score,
            exact_matches=exact,
            related_matches=related,
            verified_claim_ids=[claim.id for claim in claims],
            explanation=explanation,
        )

    async def _apply_narratives(
        self, job: Job, ranked: list[RankedPortfolioProject]
    ) -> None:
        if not self.model:
            raise ValueError("An AI model must be configured when portfolio analysis is enabled")
        allowed_projects = {item.project_id: item for item in ranked}
        serialized_rankings = [item.model_dump(mode="json") for item in ranked]
        result = await self.provider.complete_structured(
            prompt=(
                "Explain the supplied deterministic portfolio rankings without changing scores "
                "or adding experience. Cite only supplied claim IDs.\n"
                f"Job: {job.title}\nRankings: {json.dumps(serialized_rankings)}"
            ),
            response_model=PortfolioNarrativeResult,
            model=self.model,
        )
        if not isinstance(result, PortfolioNarrativeResult):
            raise InvalidStructuredOutputError("Invalid portfolio narrative response")
        if any(item.project_id not in allowed_projects for item in result.projects):
            raise UnsupportedPortfolioEvidenceError("AI referenced an unsupported project")
        for narrative in result.projects:
            permitted_claims = set(
                allowed_projects[narrative.project_id].verified_claim_ids
            )
            if set(narrative.supporting_claim_ids) - permitted_claims:
                raise UnsupportedPortfolioEvidenceError(
                    "AI referenced unsupported portfolio claims"
                )
            allowed_projects[narrative.project_id].explanation = narrative.explanation
