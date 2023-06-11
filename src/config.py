"""File with configs and settings for the project"""
import os
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get(
    'DATABASE_URL',
    default='postgresql+asyncpg://postgres:postgres@localhost:5432/postgres?async_fallback=true'
)


def get_database_info() -> dict:
    return {
        'NAME': os.environ.get('DB_NAME', default='db_name'),
        'USER': os.environ.get('DB_USER', default='postgres'),
        'PASSWORD': os.environ.get('DB_PASSWORD', default='postgres'),
        'HOST': os.environ.get('DB_HOST', default='localhost'),
        'PORT': os.environ.get('DB_PORT', default='5432')
    }


Base = declarative_base()
