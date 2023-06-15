from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from .schemas import UserShow, UserCreate
from src.database import get_database
from .utils import create_new_user, check_unique_email

user_app = FastAPI()


@user_app.post('/registration', response_model=UserShow)
async def create_user(data: UserCreate, db: AsyncSession = Depends(get_database)) -> UserShow:
    check_email = await check_unique_email(data.email, db)
    if check_email:
        raise HTTPException(status_code=400, detail='User with provided email exists!')
    try:
        return await create_new_user(data, db)
    except IntegrityError as error:
        raise HTTPException(status_code=503, detail=f'Database error: {error}')
