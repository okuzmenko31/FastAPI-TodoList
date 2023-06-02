from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from config import DATABASE_URL

engine = create_async_engine(DATABASE_URL,
                             future=True,
                             echo=True,
                             execution_options={'isolation_level': 'AUTOCOMMIT'})

session = async_sessionmaker(engine, expire_on_commit=False)
