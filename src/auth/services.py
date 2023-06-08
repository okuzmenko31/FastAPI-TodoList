from sqlalchemy.ext.asyncio import AsyncSession
from .schemas import UserCreate, UserShow
from .utils import UserManager
from .hashing import Hashing


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
            email=user.email,
            is_active=user.is_active
        )
