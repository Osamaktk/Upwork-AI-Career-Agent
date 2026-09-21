from decimal import Decimal
from pathlib import Path

from pydantic import BaseModel, Field

from app.agents.job_analyzer import JobAnalyzerAgent
from app.agents.portfolio_matcher import PortfolioMatcherAgent
from app.models.enums import VerificationStatus
from app.models.identity import VerifiedClaim
from app.models.jobs import Job
from app.models.portfolio import PortfolioProject
from app.schemas.evidence import Phase3EvaluationMetrics


class EvaluationProject(BaseModel):
    title: str
    technologies: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    verified_claims: list[str] = Field(default_factory=list)


class EvaluationCase(BaseModel):
    id: str
    category: str
    job_title: str
    job_description: str
    input_skills: list[str]
    expected_skills: list[str]
    projects: list[EvaluationProject]
    expected_projects: list[str]


class EvaluationDataset(BaseModel):
    cases: list[EvaluationCase] = Field(min_length=5)


class Phase3EvaluationService:
    async def run(self, path: Path) -> Phase3EvaluationMetrics:
        dataset = EvaluationDataset.model_validate_json(path.read_text(encoding="utf-8"))
        skill_correct = 0
        skill_total = 0
        portfolio_correct = 0
        false_matches = 0
        selected_total = 0
        unsupported_claims = 0
        cited_claims = 0
        matcher = PortfolioMatcherAgent()
        analyzer = JobAnalyzerAgent()
        for case_index, case in enumerate(dataset.cases):
            expected_skills = {item.casefold() for item in case.expected_skills}
            job = Job(
                id=f"evaluation-job-{case_index}",
                source="evaluation",
                source_job_id=case.id,
                title=case.job_title,
                description=case.job_description,
                required_skills=case.input_skills,
            )
            analysis = await analyzer.analyze(job)
            extracted_skills = {item.casefold() for item in analysis.required_skills}
            skill_correct += len(expected_skills & extracted_skills)
            skill_total += len(expected_skills | extracted_skills)
            projects: list[PortfolioProject] = []
            claims_by_project: dict[str, list[VerifiedClaim]] = {}
            allowed_claim_ids: set[str] = set()
            for project_index, project_data in enumerate(case.projects):
                project_id = f"evaluation-project-{case_index}-{project_index}"
                project = PortfolioProject(
                    id=project_id,
                    user_id="evaluation-user",
                    title=project_data.title,
                    description="Evaluation fixture",
                    technologies=project_data.technologies,
                    skills=project_data.skills,
                    verification_status=VerificationStatus.VERIFIED.value,
                )
                projects.append(project)
                claims_by_project[project_id] = []
                for claim_index, claim_text in enumerate(project_data.verified_claims):
                    claim_id = f"evaluation-claim-{case_index}-{project_index}-{claim_index}"
                    allowed_claim_ids.add(claim_id)
                    claims_by_project[project_id].append(
                        VerifiedClaim(
                            id=claim_id,
                            user_id="evaluation-user",
                            portfolio_project_id=project_id,
                            claim=claim_text,
                            category="PROJECT",
                            source="phase 3 evaluation fixture",
                            verification_status=VerificationStatus.VERIFIED.value,
                        )
                    )
            ranked = await matcher.rank(job, projects, claims_by_project)
            selected = {item.title for item in ranked}
            expected = set(case.expected_projects)
            portfolio_correct += int(selected == expected)
            false_matches += len(selected - expected)
            selected_total += len(selected)
            cited = {claim_id for item in ranked for claim_id in item.verified_claim_ids}
            unsupported_claims += len(cited - allowed_claim_ids)
            cited_claims += len(cited)
        case_count = len(dataset.cases)
        skill_accuracy = Decimal(skill_correct * 100) / Decimal(skill_total or 1)
        portfolio_accuracy = Decimal(portfolio_correct * 100) / Decimal(case_count or 1)
        unsupported_rate = Decimal(unsupported_claims * 100) / Decimal(cited_claims or 1)
        false_match_rate = Decimal(false_matches * 100) / Decimal(selected_total or 1)
        return Phase3EvaluationMetrics(
            case_count=case_count,
            skill_extraction_accuracy=skill_accuracy.quantize(Decimal("0.01")),
            portfolio_selection_accuracy=portfolio_accuracy.quantize(Decimal("0.01")),
            unsupported_claim_rate=unsupported_rate.quantize(Decimal("0.01")),
            false_match_rate=false_match_rate.quantize(Decimal("0.01")),
            passed=(
                skill_accuracy >= Decimal("90")
                and portfolio_accuracy >= Decimal("80")
                and unsupported_rate == 0
                and false_match_rate <= Decimal("10")
            ),
        )
