from pydantic import BaseModel


class DevelopmentSeedResult(BaseModel):
    profile_created: bool
    skills_created: int
    claims_created: int
    projects_created: int
    synthetic: bool = True
