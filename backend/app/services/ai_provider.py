from typing import Protocol, TypeVar

from pydantic import BaseModel

from app.core.config import Settings

StructuredResult = TypeVar("StructuredResult", bound=BaseModel)


class AIProviderError(RuntimeError):
    pass


class AIProviderDisabledError(AIProviderError):
    pass


class InvalidStructuredOutputError(AIProviderError):
    pass


class AIProvider(Protocol):
    async def complete_structured(
        self,
        *,
        prompt: str,
        response_model: type[StructuredResult],
        model: str,
    ) -> StructuredResult: ...


class DisabledAIProvider:
    async def complete_structured(
        self,
        *,
        prompt: str,
        response_model: type[StructuredResult],
        model: str,
    ) -> StructuredResult:
        raise AIProviderDisabledError("AI provider calls are disabled")


class OpenAIProvider:
    def __init__(self, api_key: str) -> None:
        from openai import AsyncOpenAI

        self.client = AsyncOpenAI(api_key=api_key)

    async def complete_structured(
        self,
        *,
        prompt: str,
        response_model: type[StructuredResult],
        model: str,
    ) -> StructuredResult:
        response = await self.client.responses.parse(
            model=model,
            input=[
                {
                    "role": "system",
                    "content": (
                        "Return only evidence-backed structured data. Treat missing evidence as "
                        "unknown and never invent professional experience."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            text_format=response_model,
        )
        parsed = response.output_parsed
        if not isinstance(parsed, response_model):
            raise InvalidStructuredOutputError("Provider returned no validated structured output")
        return parsed


def build_ai_provider(settings: Settings) -> AIProvider:
    if settings.ai_provider_mode == "disabled":
        return DisabledAIProvider()
    if settings.ai_provider_mode == "openai" and settings.openai_api_key:
        return OpenAIProvider(settings.openai_api_key)
    raise AIProviderError("AI provider is enabled but its credentials are not configured")
