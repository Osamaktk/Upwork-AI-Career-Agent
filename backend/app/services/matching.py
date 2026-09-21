import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import CompatibilityStatus, VerificationStatus
from app.models.identity import Skill, VerifiedClaim
from app.models.jobs import Job, JobMatch
from app.models.portfolio import PortfolioProject
from app.repositories.jobs import JobRepository
from app.schemas.matching import (
    JobMatchRead,
    MatchNarrative,
    RelatedMatch,
    RelationshipKind,
    SemanticRelationshipResult,
)
from app.services.ai_provider import AIProvider, DisabledAIProvider, InvalidStructuredOutputError

FORMULA_VERSION = "v1"
EXACT_SKILL_WEIGHT = Decimal("1.0")
RELATED_SKILL_WEIGHT = Decimal("0.6")
SKILL_COMPONENT = Decimal("75")
PORTFOLIO_COMPONENT = Decimal("15")
EXPERIENCE_COMPONENT = Decimal("10")

RELATED_GROUPS = (
    frozenset({"computer vision", "opencv", "image processing", "facial recognition"}),
    frozenset({"machine learning", "ml", "artificial intelligence", "ai ml"}),
    frozenset({"fastapi", "api development", "rest api", "rest apis", "backend api"}),
    frozenset({"flutter", "dart", "mobile development"}),
    frozenset({"firebase", "firestore", "backend as a service"}),
    frozenset({"python", "python programming"}),
    frozenset({"nextjs", "next js", "react", "frontend development"}),
)


class MatchNotReadyError(Exception):
    pass


class UnsupportedClaimError(Exception):
    pass


@dataclass
class MatchEvidence:
    exact: list[str]
    related: list[RelatedMatch]
    missing: list[str]
    portfolio_ids: list[str]
    claim_ids: list[str]
    concerns: list[str]


def normalize_capability(value: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9+#. ]+", " ", value.casefold()).split())


def related_capabilities(first: str, second: str) -> bool:
    left = normalize_capability(first)
    right = normalize_capability(second)
    if left == right:
        return False
    return any(left in group and right in group for group in RELATED_GROUPS)


class MatchingService:
    def __init__(
        self,
        session: AsyncSession,
        provider: AIProvider | None = None,
        model: str | None = None,
        use_ai: bool = False,
    ) -> None:
        self.session = session
        self.repository = JobRepository(session)
        self.provider = provider or DisabledAIProvider()
        self.model = model
        self.use_ai = use_ai

    async def match(self, job_id: str, user_id: str) -> JobMatchRead:
        job = await self.repository.get(job_id)
        if job is None:
            raise MatchNotReadyError("Job does not exist")
        if not (job.normalized_data or {}).get("analysis"):
            raise MatchNotReadyError("Job must be analyzed before matching")
        capabilities, claims, projects = await self._verified_context(user_id)
        evidence = self._deterministic_evidence(job, capabilities, claims, projects)
        model_used: str | None = None
        if self.use_ai:
            if not self.model:
                raise MatchNotReadyError("AI model is not configured")
            evidence = await self._apply_semantic_relationships(job, capabilities, evidence)
            explanation, ai_concerns, narrative_claim_ids = await self._ai_narrative(
                job, evidence, claims
            )
            evidence.concerns.extend(item for item in ai_concerns if item not in evidence.concerns)
            evidence.claim_ids = sorted(set(evidence.claim_ids) | set(narrative_claim_ids))
            model_used = self.model
        else:
            explanation = self._deterministic_explanation(job, evidence)
        score = self._score(job.required_skills, evidence)
        match = await self.repository.get_match(job.id, user_id)
        values = {
            "compatibility_score": score,
            "matching_skills": evidence.exact,
            "exact_matches": evidence.exact,
            "related_matches": [item.model_dump() for item in evidence.related],
            "missing_skills": evidence.missing,
            "portfolio_project_ids": evidence.portfolio_ids,
            "relevant_claim_ids": evidence.claim_ids,
            "concerns": evidence.concerns,
            "reasons": self._reasons(evidence),
            "recommended_next_action": (
                "Review skill gaps before drafting a proposal"
                if evidence.missing
                else "Review the matched evidence before drafting a proposal"
            ),
            "explanation": explanation,
            "model_used": model_used,
            "formula_version": FORMULA_VERSION,
            "analysis_timestamp": datetime.now(UTC),
        }
        if match is None:
            match = JobMatch(job_id=job.id, user_id=user_id, **values)
            self.session.add(match)
        else:
            for key, value in values.items():
                setattr(match, key, value)
        job.compatibility_status = CompatibilityStatus.MATCHED.value
        await self.session.commit()
        await self.session.refresh(match)
        return JobMatchRead.model_validate(match)

    async def _verified_context(
        self, user_id: str
    ) -> tuple[list[str], list[VerifiedClaim], list[PortfolioProject]]:
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
        project_result = await self.session.execute(
            select(PortfolioProject).where(
                PortfolioProject.user_id == user_id,
                PortfolioProject.is_active.is_(True),
                PortfolioProject.verification_status == VerificationStatus.VERIFIED.value,
            )
        )
        claims = list(claims_result.scalars())
        capabilities = [skill.name for skill in skills_result.scalars()]
        capabilities.extend(claim.claim for claim in claims if claim.category == "SKILL")
        unique = list(dict.fromkeys(capabilities))
        return unique, claims, list(project_result.scalars())

    def _deterministic_evidence(
        self,
        job: Job,
        capabilities: list[str],
        claims: list[VerifiedClaim],
        projects: list[PortfolioProject],
    ) -> MatchEvidence:
        exact: list[str] = []
        related: list[RelatedMatch] = []
        missing: list[str] = []
        for required in job.required_skills:
            exact_capability = next(
                (
                    capability
                    for capability in capabilities
                    if normalize_capability(capability) == normalize_capability(required)
                ),
                None,
            )
            if exact_capability:
                exact.append(required)
                continue
            related_capability = next(
                (
                    capability
                    for capability in capabilities
                    if related_capabilities(required, capability)
                ),
                None,
            )
            if related_capability:
                related.append(
                    RelatedMatch(required_skill=required, evidence=related_capability)
                )
            else:
                missing.append(required)
        matched_projects = [
            project.id
            for project in projects
            if any(
                normalize_capability(requirement) == normalize_capability(capability)
                or related_capabilities(requirement, capability)
                for requirement in job.required_skills
                for capability in [*project.technologies, *project.skills]
            )
        ]
        relevant_claims = [
            claim.id
            for claim in claims
            if claim.category != "SKILL"
            and any(
                normalize_capability(requirement) in normalize_capability(claim.claim)
                or related_capabilities(requirement, claim.claim)
                for requirement in job.required_skills
            )
        ]
        concerns = [f"Missing verified skill: {skill}" for skill in missing]
        if not capabilities:
            concerns.append("No verified skills are available for matching.")
        return MatchEvidence(
            exact=exact,
            related=related,
            missing=missing,
            portfolio_ids=matched_projects,
            claim_ids=relevant_claims,
            concerns=concerns,
        )

    async def _apply_semantic_relationships(
        self, job: Job, capabilities: list[str], evidence: MatchEvidence
    ) -> MatchEvidence:
        if not evidence.missing:
            return evidence
        result = await self.provider.complete_structured(
            prompt=(
                "Classify relationships between each missing requirement and the verified "
                "capabilities. UNKNOWN must stay unknown.\n"
                f"Requirements: {json.dumps(evidence.missing)}\n"
                f"Verified capabilities: {json.dumps(capabilities)}"
            ),
            response_model=SemanticRelationshipResult,
            model=self.model or "",
        )
        if not isinstance(result, SemanticRelationshipResult):
            raise InvalidStructuredOutputError("Invalid semantic relationship response")
        missing_by_key = {normalize_capability(item): item for item in evidence.missing}
        capability_by_key = {normalize_capability(item): item for item in capabilities}
        promoted: set[str] = set()
        for relationship in result.relationships:
            key = normalize_capability(relationship.required_skill)
            if key not in missing_by_key:
                raise UnsupportedClaimError("AI referenced an unknown job requirement")
            if relationship.relationship == RelationshipKind.RELATED_MATCH:
                capability_key = normalize_capability(relationship.capability or "")
                if capability_key not in capability_by_key:
                    raise UnsupportedClaimError("AI referenced an unverified capability")
                evidence.related.append(
                    RelatedMatch(
                        required_skill=missing_by_key[key],
                        evidence=capability_by_key[capability_key],
                    )
                )
                promoted.add(key)
            elif relationship.relationship == RelationshipKind.UNKNOWN:
                evidence.concerns.append(
                    f"Unknown relationship for {missing_by_key[key]}: {relationship.reason}"
                )
        evidence.missing = [
            item for item in evidence.missing if normalize_capability(item) not in promoted
        ]
        return evidence

    async def _ai_narrative(
        self, job: Job, evidence: MatchEvidence, claims: list[VerifiedClaim]
    ) -> tuple[str, list[str], list[str]]:
        allowed_claims = {claim.id: claim.claim for claim in claims}
        result = await self.provider.complete_structured(
            prompt=(
                "Explain this deterministic match without changing the score or adding facts. "
                "Every factual experience statement must cite a supplied claim ID.\n"
                f"Job: {job.title}\nEvidence: {json.dumps(evidence.__dict__, default=str)}\n"
                f"Verified claims: {json.dumps(allowed_claims)}"
            ),
            response_model=MatchNarrative,
            model=self.model or "",
        )
        if not isinstance(result, MatchNarrative):
            raise InvalidStructuredOutputError("Invalid match narrative response")
        unsupported = set(result.supporting_claim_ids) - set(allowed_claims)
        if unsupported:
            raise UnsupportedClaimError("AI explanation cited unsupported claims")
        return result.explanation, result.concerns, result.supporting_claim_ids

    @staticmethod
    def _score(requirements: list[str], evidence: MatchEvidence) -> Decimal:
        skill_score = Decimal("0")
        if requirements:
            weighted = Decimal(len(evidence.exact)) * EXACT_SKILL_WEIGHT
            weighted += Decimal(len(evidence.related)) * RELATED_SKILL_WEIGHT
            skill_score = SKILL_COMPONENT * weighted / Decimal(len(requirements))
        portfolio_score = PORTFOLIO_COMPONENT if evidence.portfolio_ids else Decimal("0")
        experience_score = EXPERIENCE_COMPONENT if evidence.claim_ids else Decimal("0")
        return min(Decimal("100"), skill_score + portfolio_score + experience_score).quantize(
            Decimal("0.01")
        )

    @staticmethod
    def _deterministic_explanation(job: Job, evidence: MatchEvidence) -> str:
        parts = [f"The match for {job.title} uses verified evidence only."]
        if evidence.exact:
            parts.append(f"Exact skills: {', '.join(evidence.exact)}.")
        if evidence.related:
            rendered = ", ".join(
                f"{item.required_skill} via {item.evidence}" for item in evidence.related
            )
            parts.append(f"Related capabilities: {rendered}.")
        if evidence.missing:
            parts.append(f"Unverified or missing skills: {', '.join(evidence.missing)}.")
        if evidence.portfolio_ids:
            parts.append("At least one verified portfolio project overlaps the requirements.")
        return " ".join(parts)

    @staticmethod
    def _reasons(evidence: MatchEvidence) -> list[str]:
        reasons = [f"Exact match: {item}" for item in evidence.exact]
        reasons.extend(
            f"Related match: {item.required_skill} via {item.evidence}"
            for item in evidence.related
        )
        reasons.extend(f"Missing: {item}" for item in evidence.missing)
        return reasons
