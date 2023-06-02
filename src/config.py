"""File with configs and settings for the project"""
from envparse import Env
from sqlalchemy.orm import declarative_base

env = Env()

DATABASE_URL = env.str(
    'DATABASE_URL',
    default='postgresql+asyncpg://postgres:postgres@localhost:5432/postgres'
)


def get_database_info() -> dict:
    return {
        'NAME': env.str('DB_NAME', default='db_name'),
        'USER': env.str('DB_USER', default='postgres'),
        'PASSWORD': env.str('DB_PASSWORD', default='postgres'),
        'HOST': env.str('DB_HOST', default='localhost'),
        'PORT': env.str('DB_PORT', default='5432')
    }


Base = declarative_base()
