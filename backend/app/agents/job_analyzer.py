import re
from decimal import Decimal

from app.models.jobs import Job
from app.schemas.jobs import JobAnalysis
from app.services.ai_provider import AIProvider, DisabledAIProvider

COMPLEXITY_TERMS = (
    "production",
    "asynchronous",
    "retries",
    "audit",
    "machine learning",
    "computer vision",
    "structured output",
    "security",
    "distributed",
)


class JobAnalyzerAgent:
    def __init__(
        self,
        provider: AIProvider | None = None,
        model: str | None = None,
        use_ai: bool = False,
    ) -> None:
        self.provider = provider or DisabledAIProvider()
        self.model = model
        self.use_ai = use_ai

    async def analyze(self, job: Job) -> JobAnalysis:
        if self.use_ai:
            if not self.model:
                raise ValueError("An AI model must be configured when AI analysis is enabled")
            result = await self.provider.complete_structured(
                prompt=self._prompt(job), response_model=JobAnalysis, model=self.model
            )
            if not isinstance(result, JobAnalysis):
                raise TypeError("AI provider returned an invalid JobAnalysis result")
            return result
        return self._deterministic_analysis(job)

    def _deterministic_analysis(self, job: Job) -> JobAnalysis:
        text = job.description.strip()
        sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if part.strip()]
        action_sentences = [
            sentence
            for sentence in sentences
            if re.search(
                r"\b(build|create|design|implement|develop|detect|return|include)\b",
                sentence,
                re.I,
            )
        ]
        unclear: list[str] = []
        questions: list[str] = []
        if not job.required_skills:
            unclear.append("No explicit required skills were supplied.")
            questions.append("Which skills and technologies are mandatory?")
        if not re.search(r"\b(day|week|month|deadline|timeline)\b", text, re.I):
            unclear.append("The delivery timeline is not explicit.")
            questions.append("What delivery date or milestone schedule should be used?")
        if job.budget_min is None and job.budget_max is None:
            unclear.append("The budget is not specified.")
            questions.append("What budget range has been approved?")
        budget = self._format_budget(job.budget_min, job.budget_max, job.currency)
        complexity = [term for term in COMPLEXITY_TERMS if term in text.casefold()]
        return JobAnalysis(
            required_skills=job.required_skills,
            preferred_skills=[],
            technologies=job.required_skills,
            responsibilities=action_sentences,
            deliverables=action_sentences,
            experience_requirement=self._extract_experience(text),
            timeline=self._extract_timeline(text),
            budget=budget,
            project_type=job.budget_type,
            complexity_indicators=complexity,
            unclear_requirements=unclear,
            questions=questions,
        )

    @staticmethod
    def _extract_experience(text: str) -> str | None:
        match = re.search(r"\b\d+\+?\s+years?[^.,;]*", text, re.I)
        return match.group(0) if match else None

    @staticmethod
    def _extract_timeline(text: str) -> str | None:
        match = re.search(r"\b(?:within\s+)?\d+\s+(?:days?|weeks?|months?)\b", text, re.I)
        return match.group(0) if match else None

    @staticmethod
    def _format_budget(
        minimum: Decimal | None, maximum: Decimal | None, currency: str | None
    ) -> str | None:
        if minimum is None and maximum is None:
            return None
        unit = currency or ""
        if minimum is not None and maximum is not None:
            return f"{unit} {minimum}-{maximum}".strip()
        value = minimum if minimum is not None else maximum
        return f"{unit} {value}".strip()

    @staticmethod
    def _prompt(job: Job) -> str:
        return (
            "Analyze this normalized job into the requested schema. Do not infer unsupported "
            f"experience requirements.\nTitle: {job.title}\nDescription: {job.description}\n"
            f"Skills: {job.required_skills}\nBudget: {job.budget_min}-{job.budget_max}"
        )
