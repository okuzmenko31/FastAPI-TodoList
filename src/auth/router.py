from typing import Union

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from .schemas import UserShow, UserCreate
from src.database import get_database
from .utils import create_new_user, check_unique_email, UserManager
from .token import AuthTokenManager, get_token_data

user_app = FastAPI()


@user_app.post('/registration', response_model=UserShow)
async def create_user(data: UserCreate, session: AsyncSession = Depends(get_database)) -> UserShow:
    check_email = await check_unique_email(data.email, session)
    if check_email:
        raise HTTPException(status_code=400, detail='User with provided email exists!')
    token_manager = AuthTokenManager(session=session)
    token_manager.token_type = 'su'
    try:
        user = await create_new_user(data, session)
        await token_manager.send_tokenized_mail(data.email)
        return user
    except IntegrityError as error:
        raise HTTPException(status_code=503, detail=f'Database error: {error}')


@user_app.post('/confirm_email_reg/{token}/{email}')
async def confirm_email_and_register(token: str,
                                     email: str,
                                     session: AsyncSession = Depends(get_database)) -> Union[UserShow, str]:
    async with session.begin():
        token_data = await get_token_data(token, email, session)
        if token_data.token:
            user_manager = UserManager(session=session)
            user = await user_manager.get_user_by_email(email)
            user.is_active = True
            await session.commit()
            return UserShow(
                id=user.id,
                name=user.name,
                surname=user.surname,
                email=user.email,
                username=user.username,
                is_active=user.is_active
            )
        raise HTTPException(
            status_code=400,
            detail=token_data.error
        )


@user_app.get('/users', response_model=list[UserShow])
async def get_all_users(session: AsyncSession = Depends(get_database)) -> list[UserShow]:
    manager = UserManager(session)
    async with session.begin():
        users = await manager.get_all_users()
        users_lst = []
        for obj in users:
            user = obj[0]
            show = UserShow(
                id=user.id,
                name=user.name,
                surname=user.surname,
                email=user.email,
                username=user.username,
                is_active=user.is_active
            )
            users_lst.append(show)
        return users_lst
