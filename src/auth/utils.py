from sqlalchemy.ext.asyncio import AsyncSession
from .models import Roles, User
from sqlalchemy import select, delete, exists
from sqlalchemy.dialects.postgresql import UUID
from typing import Union


def username_from_email(email: str):
    return '@' + email.split('@')[0]


class UserManager:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def _check_user_exists(self, username, suffix=None) -> bool:
        query = select(User).where(User.username == username + str(suffix))
        if suffix is not None:
            query = select(User).where(User.username == username)
        exist_query = exists(query).select()
        result = await self.session.execute(exist_query)
        exists_row = result.fetchone()
        return exists_row[0]

    async def generate_username(self, email: str) -> str:
        if not email:
            raise ValueError('Email must be provided!')
        username = username_from_email(email)
        exist_by_username = await self._check_user_exists(username)
        if not exist_by_username:
            return username
        suffix = 1
        exist_by_username_and_suffix = await self._check_user_exists(username, suffix=suffix)
        while exist_by_username_and_suffix:
            suffix += 1
        return username + str(suffix)

    async def create_user(self,
                          name: str,
                          surname: str,
                          email: str,
                          password: str) -> User:
        username = await self.generate_username(email)
        roles = [Roles.role_user]
        new_user = User(name=name,
                        surname=surname,
                        email=email,
                        username=username,
                        hashed_password=password,
                        roles=roles)
        self.session.add(new_user)
        await self.session.flush()
        return new_user

    async def delete_user(self, user_id: UUID) -> Union[UUID, None]:
        query = delete(User).where(User.id == user_id).returning(User.id)
        result = await self.session.execute(query)
        deleted_user_row = result.fetchone()
        if deleted_user_row is not None:
            return deleted_user_row[0]

    async def get_user_by_id(self, user_id: UUID) -> Union[User, None]:
        query = select(User).where(User.id == user_id)
        result = await self.session.execute(query)
        user_row = result.fetchone()
        if user_row is not None:
            return user_row[0]

    async def get_user_by_username(self, username) -> Union[User, None]:
        query = select(User).where(User.username == username)
        result = await self.session.execute(query)
        user_row = result.fetchone()
        if user_row is not None:
            return user_row[0]

    async def get_user_by_email(self, email):
        query = select(User).where(User.email == email)
        result = await self.session.execute(query)
        user_row = result.fetchone()
        if user_row is not None:
            return user_row[0]