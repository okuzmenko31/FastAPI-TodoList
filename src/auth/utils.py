from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from .hashing import Hashing
from .models import Roles, User, JwtTokensBlackList
from sqlalchemy import select, delete, exists
from sqlalchemy.dialects.postgresql import UUID
from typing import Union
from .schemas import UserCreate, UserShow, TokenData
from src.config import SECRET_KEY
from src.database.core import get_database


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

    async def get_all_users(self):
        query = select(User).filter_by(is_active=True)
        result = await self.session.execute(query)
        users_row = result.fetchall()
        return users_row


async def create_new_user(data: UserCreate, session: AsyncSession) -> UserShow:
    async with session.begin():
        manager = UserManager(session=session)
        user = await manager.create_user(
            name=data.name,
            surname=data.surname,
            email=data.email,
            password=Hashing.get_hashed_password(data.password)
        )
        return UserShow(
            id=user.id,
            name=user.name,
            surname=user.surname,
            username=user.username,
            email=user.email,
            is_active=user.is_active
        )


async def check_unique_email(email: str, session: AsyncSession) -> bool:
    async with session.begin():
        query = select(User).where(User.email == email)
        exist_query = exists(query).select()
        result = await session.execute(exist_query)
        exists_row = result.fetchone()
        return exists_row[0]


async def authenticate_user(username: str,
                            password: str,
                            session: AsyncSession = Depends(get_database)):
    manager = UserManager(session=session)
    async with session.begin():
        user = await manager.get_user_by_username(username=username)
        if not user:
            return False
        if not user.is_active:
            return False
        if not Hashing.verify_password(password=password, hashed_password=user.hashed_password):
            return False
        return user


async def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm='HS256')
    return encoded_jwt


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def get_current_user(session: AsyncSession = Depends(get_database),
                           token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        username: str = payload.get('sub')
        if username is None:
            raise credentials_exception
        token_in_black_list = await find_black_list_token(token=token,
                                                          session=session)
        if token_in_black_list:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    manager = UserManager(session=session)
    async with session.begin():
        user = await manager.get_user_by_username(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user=Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail='Inactive user')
    return current_user


async def add_jwt_token_to_blacklist(token: str,
                                     email: str,
                                     session: AsyncSession):
    blacklist_token = JwtTokensBlackList(token=token, email=email)
    async with session.begin():
        session.add(blacklist_token)
        await session.flush()


async def find_black_list_token(token: str,
                                session: AsyncSession):
    query = select(JwtTokensBlackList).where(JwtTokensBlackList.token == token)
    exist_query = exists(query).select()
    async with session.begin():
        result = await session.execute(exist_query)
        exists_row = result.fetchone()
        return exists_row[0]


async def get_token_user(token: str = Depends(oauth2_scheme)):
    return token
