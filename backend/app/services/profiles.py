from sqlalchemy.ext.asyncio import AsyncSession

from app.models.identity import Profile
from app.repositories.profiles import ProfileRepository
from app.schemas.profile import ProfileCreate, ProfileRead, ProfileUpdate

SKILL_FIELDS = {
    "primary_skills": "PRIMARY",
    "secondary_skills": "SECONDARY",
    "programming_languages": "LANGUAGE",
    "frameworks": "FRAMEWORK",
    "tools": "TOOL",
    "domains": "DOMAIN",
}


class ProfileAlreadyExistsError(Exception):
    pass


class ProfileNotFoundError(Exception):
    pass


def profile_completeness(profile: Profile | None) -> int:
    if profile is None:
        return 0
    fields = (
        profile.title,
        profile.overview,
        profile.location,
        profile.years_experience,
        profile.education,
        profile.certifications,
        profile.primary_skills,
        profile.secondary_skills,
        profile.programming_languages,
        profile.frameworks,
        profile.tools,
        profile.domains,
        profile.work_experience,
        profile.internships,
        profile.achievements,
    )
    completed = sum(value is not None and value != [] and value != "" for value in fields)
    return round(completed / len(fields) * 100)


def profile_to_schema(profile: Profile) -> ProfileRead:
    values = {column.name: getattr(profile, column.name) for column in profile.__table__.columns}
    return ProfileRead.model_validate({**values, "completeness": profile_completeness(profile)})


class ProfileService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = ProfileRepository(session)

    async def create(self, user_id: str, payload: ProfileCreate) -> ProfileRead:
        if await self.repository.get_for_user(user_id):
            raise ProfileAlreadyExistsError
        values = payload.model_dump(mode="json")
        profile = Profile(user_id=user_id, **values)
        self.session.add(profile)
        await self._sync_skills(user_id, values)
        await self.session.commit()
        await self.session.refresh(profile)
        return profile_to_schema(profile)

    async def get(self, user_id: str) -> ProfileRead:
        profile = await self.repository.get_for_user(user_id)
        if profile is None:
            raise ProfileNotFoundError
        return profile_to_schema(profile)

    async def update(self, user_id: str, payload: ProfileUpdate) -> ProfileRead:
        profile = await self.repository.get_for_user(user_id)
        if profile is None:
            raise ProfileNotFoundError
        values = payload.model_dump(exclude_unset=True, mode="json")
        for key, value in values.items():
            setattr(profile, key, value)
        await self._sync_skills(user_id, values)
        await self.session.commit()
        await self.session.refresh(profile)
        return profile_to_schema(profile)

    async def _sync_skills(self, user_id: str, values: dict) -> None:
        for field, category in SKILL_FIELDS.items():
            if field in values:
                await self.repository.replace_skill_category(user_id, category, values[field])
