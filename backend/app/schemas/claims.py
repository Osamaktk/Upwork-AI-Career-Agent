from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ClaimCategory, VerificationStatus


class ClaimCreate(BaseModel):
    claim: str = Field(min_length=1, max_length=4000)
    category: ClaimCategory = ClaimCategory.OTHER
    source: str = Field(min_length=1, max_length=4000)
    notes: str | None = Field(default=None, max_length=4000)
    profile_id: str | None = None
    portfolio_project_id: str | None = None
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED


class ClaimUpdate(BaseModel):
    claim: str | None = Field(default=None, min_length=1, max_length=4000)
    category: ClaimCategory | None = None
    source: str | None = Field(default=None, min_length=1, max_length=4000)
    notes: str | None = Field(default=None, max_length=4000)
    profile_id: str | None = None
    portfolio_project_id: str | None = None


class ClaimRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    profile_id: str | None
    portfolio_project_id: str | None
    claim: str
    category: ClaimCategory
    source: str
    notes: str | None
    verification_status: VerificationStatus
    created_at: datetime
    updated_at: datetime
