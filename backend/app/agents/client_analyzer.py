import json

from app.models.enums import FactClassification, VerificationStatus
from app.models.jobs import Client, ClientFact, Job
from app.schemas.clients import AnalysisStatement, ClientAnalysisDraft
from app.services.ai_provider import AIProvider, DisabledAIProvider, InvalidStructuredOutputError

PROMPT_VERSION = "client-analysis-v1"


class UnsupportedClientEvidenceError(ValueError):
    pass


class ClientAnalyzerAgent:
    def __init__(
        self,
        provider: AIProvider | None = None,
        model: str | None = None,
        use_ai: bool = False,
    ) -> None:
        self.provider = provider or DisabledAIProvider()
        self.model = model
        self.use_ai = use_ai

    async def analyze(
        self, client: Client, job: Job, facts: list[ClientFact]
    ) -> ClientAnalysisDraft:
        if not self.use_ai:
            return self._deterministic(client, job, facts)
        if not self.model:
            raise ValueError("An AI model must be configured when client analysis is enabled")
        result = await self.provider.complete_structured(
            prompt=self._prompt(client, job, facts),
            response_model=ClientAnalysisDraft,
            model=self.model,
        )
        if not isinstance(result, ClientAnalysisDraft):
            raise InvalidStructuredOutputError("Invalid client analysis response")
        self._validate_evidence(result, facts)
        return result

    @staticmethod
    def _deterministic(
        client: Client, job: Job, facts: list[ClientFact]
    ) -> ClientAnalysisDraft:
        verified_facts = [
            fact
            for fact in facts
            if fact.classification == FactClassification.FACT.value
            and fact.verification_status == VerificationStatus.VERIFIED.value
        ]
        unknowns: list[str] = []
        questions: list[str] = []
        if not client.company:
            unknowns.append("The client's company is not verified.")
        if not client.website:
            unknowns.append("A public company website is not available.")
        if not any(fact.fact_type.casefold() == "hiring" for fact in verified_facts):
            unknowns.append("Verified hiring history is unavailable.")
        if job.budget_min is None and job.budget_max is None:
            questions.append("What budget range has been approved for this project?")
        analysis = (job.normalized_data or {}).get("analysis") or {}
        questions.extend(analysis.get("questions", []))
        concerns = [
            AnalysisStatement(text=item, supporting_fact_ids=[])
            for item in analysis.get("unclear_requirements", [])
        ]
        style = [
            AnalysisStatement(text=fact.fact, supporting_fact_ids=[fact.id])
            for fact in verified_facts
            if fact.fact_type.casefold() in {"communication", "communication_style"}
        ]
        return ClientAnalysisDraft(
            inferences=[],
            unknowns=list(dict.fromkeys(unknowns)),
            project_goals=[
                AnalysisStatement(
                    text=f"Deliver the requested outcome for: {job.title}.",
                    supporting_fact_ids=[],
                )
            ],
            requirements=list(job.required_skills),
            concerns=concerns,
            questions=list(dict.fromkeys(questions)),
            communication_style_indicators=style,
        )

    @staticmethod
    def _validate_evidence(result: ClientAnalysisDraft, facts: list[ClientFact]) -> None:
        allowed = {fact.id for fact in facts}
        statements = [
            *result.inferences,
            *result.project_goals,
            *result.concerns,
            *result.communication_style_indicators,
        ]
        cited = {fact_id for statement in statements for fact_id in statement.supporting_fact_ids}
        if cited - allowed:
            raise UnsupportedClientEvidenceError("Client analysis cited unsupported facts")
        if any(not statement.supporting_fact_ids for statement in result.inferences):
            raise UnsupportedClientEvidenceError("Client inferences require supporting fact IDs")
        if any(
            not statement.supporting_fact_ids
            for statement in result.communication_style_indicators
        ):
            raise UnsupportedClientEvidenceError(
                "Communication-style indicators require supporting fact IDs"
            )

    @staticmethod
    def _prompt(client: Client, job: Job, facts: list[ClientFact]) -> str:
        permitted = [
            {
                "id": fact.id,
                "text": fact.fact,
                "classification": fact.classification,
                "verification_status": fact.verification_status,
            }
            for fact in facts
        ]
        job_context = {
            "title": job.title,
            "description": job.description,
            "skills": job.required_skills,
        }
        return (
            "Analyze the client and job without sensitive-trait speculation or invented facts. "
            "Put uncertain interpretations in inferences, cite their supplied fact IDs, and put "
            "missing information in unknowns. Communication indicators require fact IDs.\n"
            f"Client: {json.dumps({'name': client.name, 'company': client.company})}\n"
            f"Job: {json.dumps(job_context)}\n"
            f"Permitted facts: {json.dumps(permitted)}"
        )
