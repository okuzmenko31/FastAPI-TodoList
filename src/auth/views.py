from datetime import timedelta
from typing import Union

from fastapi import Depends, HTTPException, status, APIRouter
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from .schemas import UserShow, UserCreate, Token
from src.database.core import get_database
from .utils import (create_new_user,
                    check_unique_email,
                    UserManager,
                    authenticate_user,
                    get_current_active_user,
                    create_access_token,
                    add_jwt_token_to_blacklist,
                    get_token_user)
from .token import AuthTokenManager, get_token_data

router = APIRouter(
    prefix='/users',
    tags=['Users']
)


@router.post('/registration/', response_model=UserShow)
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


@router.post('/confirm_email_reg/{token}/{email}/')
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


@router.post('/token/', response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(),
                                 session: AsyncSession = Depends(get_database)):
    user = await authenticate_user(session=session,
                                   username=form_data.username,
                                   password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=30)
    access_token = await create_access_token(data={'sub': user.username},
                                             expires_delta=access_token_expires)
    return {'access_token': access_token, 'token_type': 'bearer'}


@router.get('/logout/')
async def logout(session: AsyncSession = Depends(get_database),
                 token: str = Depends(get_token_user),
                 current_user=Depends(get_current_active_user)):
    await add_jwt_token_to_blacklist(session=session,
                                     token=token,
                                     email=current_user.email)
    return {
        'status_code': status.HTTP_200_OK,
        'detail': 'You successfully logged out.'
    }


@router.get("/me/", response_model=UserShow)
async def read_users_me(current_user=Depends(get_current_active_user)):
    return current_user


@router.get('/all/', response_model=list[UserShow])
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
