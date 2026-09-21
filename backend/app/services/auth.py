from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.security import create_access_token, hash_password, verify_password
from app.models.identity import User
from app.repositories.users import UserRepository


class EmailAlreadyRegisteredError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


class AuthService:
    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self.session = session
        self.settings = settings
        self.users = UserRepository(session)

    async def register(self, email: str, password: str) -> User:
        if await self.users.get_by_email(email):
            raise EmailAlreadyRegisteredError
        user = User(email=email, password_hash=hash_password(password))
        self.users.add(user)
        try:
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise EmailAlreadyRegisteredError from exc
        await self.session.refresh(user)
        return user

    async def authenticate(self, email: str, password: str) -> str:
        user = await self.users.get_by_email(email)
        if user is None or not user.is_active or not verify_password(password, user.password_hash):
            raise InvalidCredentialsError
        return create_access_token(user.id, self.settings)
