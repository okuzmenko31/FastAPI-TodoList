from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from typing import AsyncGenerator

from .config import DATABASE_URL

engine = create_async_engine(DATABASE_URL,
                             future=True,
                             echo=True,
                             execution_options={'isolation_level': 'AUTOCOMMIT'})

session = async_sessionmaker(engine, expire_on_commit=False)


async def get_database() -> AsyncGenerator[AsyncSession, None]:
    async with session() as async_session:
        yield async_session
