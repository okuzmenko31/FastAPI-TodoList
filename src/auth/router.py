from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from .schemas import UserShow, UserCreate
from src.database import get_database
from .utils import create_new_user, check_unique_email, UserManager

user_app = FastAPI()


@user_app.post('/registration', response_model=UserShow)
async def create_user(data: UserCreate, session: AsyncSession = Depends(get_database)) -> UserShow:
    check_email = await check_unique_email(data.email, session)
    if check_email:
        raise HTTPException(status_code=400, detail='User with provided email exists!')
    try:
        return await create_new_user(data, session)
    except IntegrityError as error:
        raise HTTPException(status_code=503, detail=f'Database error: {error}')


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
