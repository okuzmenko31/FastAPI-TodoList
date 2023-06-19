"""File with configs and settings for the project"""
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.environ.get('SECRET_KEY', 'your_secret_key')

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


SMTP_HOST = os.environ.get('EMAIL_HOST')
SMTP_USER = os.environ.get('EMAIL_HOST_USER')
SMTP_USERNAME = SMTP_USER.split('@')[0]
SMTP_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
SMTP_PORT = os.environ.get('EMAIL_PORT')
