from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.identity import Profile, Skill


class ProfileRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_for_user(self, user_id: str) -> Profile | None:
        result = await self.session.execute(select(Profile).where(Profile.user_id == user_id))
        return result.scalar_one_or_none()

    async def get_skills(self, user_id: str) -> list[Skill]:
        result = await self.session.execute(
            select(Skill).where(Skill.user_id == user_id).order_by(Skill.category, Skill.name)
        )
        return list(result.scalars())

    async def replace_skill_category(
        self, user_id: str, category: str, names: list[str]
    ) -> None:
        result = await self.session.execute(
            select(Skill).where(Skill.user_id == user_id, Skill.category == category)
        )
        existing = {skill.name.casefold(): skill for skill in result.scalars()}
        requested = {name.casefold(): name for name in names}
        removable = [skill.id for key, skill in existing.items() if key not in requested]
        if removable:
            await self.session.execute(delete(Skill).where(Skill.id.in_(removable)))
        for key, display_name in requested.items():
            if key in existing:
                existing[key].name = display_name
            else:
                self.session.add(Skill(user_id=user_id, name=display_name, category=category))
