from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator

from app.models.enums import FactClassification, VerificationStatus


class ClientCreate(BaseModel):
    source: str = Field(min_length=1, max_length=80)
    source_client_id: str = Field(min_length=1, max_length=240)
    name: str | None = Field(default=None, max_length=240)
    company: str | None = Field(default=None, max_length=240)
    website: HttpUrl | None = None
    summary: str | None = Field(default=None, max_length=8000)


class ClientUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=240)
    company: str | None = Field(default=None, max_length=240)
    website: HttpUrl | None = None
    summary: str | None = Field(default=None, max_length=8000)


class ClientRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    source: str
    source_client_id: str | None
    name: str | None
    company: str | None
    website: str | None
    summary: str | None
    created_at: datetime
    updated_at: datetime


class ClientSourceCreate(BaseModel):
    source_type: str = Field(min_length=1, max_length=80)
    url: HttpUrl | None = None
    collected_at: datetime | None = None


class ClientSourceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    client_id: str
    source_type: str
    url: str | None
    collected_at: datetime | None
    created_at: datetime
    updated_at: datetime


class ClientFactCreate(BaseModel):
    client_source_id: str | None = None
    fact: str = Field(min_length=1, max_length=8000)
    fact_type: str = Field(min_length=1, max_length=80)
    classification: FactClassification
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED
    first_seen: datetime | None = None
    last_seen: datetime | None = None

    @model_validator(mode="after")
    def validate_evidence_state(self):
        if self.classification == FactClassification.FACT:
            if not self.client_source_id:
                raise ValueError("FACT records require a source")
            if self.verification_status != VerificationStatus.VERIFIED:
                raise ValueError("FACT records must be VERIFIED")
        elif self.verification_status == VerificationStatus.VERIFIED:
            raise ValueError("Only FACT records may be VERIFIED")
        if self.first_seen and self.last_seen and self.first_seen > self.last_seen:
            raise ValueError("first_seen cannot be after last_seen")
        return self


class ClientFactRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    client_id: str
    client_source_id: str | None
    fact: str
    fact_type: str
    classification: FactClassification
    verification_status: VerificationStatus
    first_seen: datetime
    last_seen: datetime
    source_type: str | None = None
    source_url: str | None = None
    created_at: datetime
    updated_at: datetime


class ClientFactReference(BaseModel):
    id: str
    fact: str
    fact_type: str
    source_id: str
    source_url: str | None = None


class AnalysisStatement(BaseModel):
    text: str = Field(min_length=1, max_length=4000)
    supporting_fact_ids: list[str] = Field(default_factory=list, max_length=50)


class ClientAnalysisDraft(BaseModel):
    inferences: list[AnalysisStatement] = Field(default_factory=list, max_length=50)
    unknowns: list[str] = Field(default_factory=list, max_length=50)
    project_goals: list[AnalysisStatement] = Field(default_factory=list, max_length=50)
    requirements: list[str] = Field(default_factory=list, max_length=100)
    concerns: list[AnalysisStatement] = Field(default_factory=list, max_length=50)
    questions: list[str] = Field(default_factory=list, max_length=50)
    communication_style_indicators: list[AnalysisStatement] = Field(
        default_factory=list, max_length=50
    )


class ClientAnalysisRead(ClientAnalysisDraft):
    model_config = ConfigDict(from_attributes=True)

    id: str
    client_id: str
    job_id: str
    verified_facts: list[ClientFactReference]
    model_used: str | None
    prompt_version: str
    analyzed_at: datetime
    created_at: datetime
    updated_at: datetime


class ClientDetail(ClientRead):
    sources: list[ClientSourceRead]
    facts: list[ClientFactRead]
    analyses: list[ClientAnalysisRead]
