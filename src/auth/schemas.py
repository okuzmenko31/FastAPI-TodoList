import re
import uuid

from pydantic import BaseModel, EmailStr, validator
from fastapi import HTTPException
from .services import validate_password

LETTERS_PATTERN = re.compile(r"^[а-яА-Яa-zA-Z\-]+$")
EN_LOWER_LETTERS_PATTERN = re.compile(r"^[a-z0-9]+$")


class MainModel(BaseModel):
    class Config:
        orm_mode = True


class UserCreate(BaseModel):
    name: str
    surname: str
    email: EmailStr
    password: str
    password_confirm: str

    @validator('name')
    def validate_name(cls, value):
        if not LETTERS_PATTERN.match(value):
            raise HTTPException(
                status_code=400,
                detail='Name should contains only letters!'
            )
        return value

    @validator('surname')
    def validate_surname(cls, value):
        if not LETTERS_PATTERN.match(value):
            raise HTTPException(
                status_code=400,
                detail='Surname should contains only letters!'
            )
        return value

    @validator('password')
    def validate_password(cls, value):
        error, success = validate_password(value)
        if not success and error:
            raise HTTPException(
                status_code=400,
                detail=error
            )
        return value

    @validator('password_confirm')
    def validate_password_confirm(cls, value, values):
        if not value == values.get('password'):
            raise HTTPException(
                status_code=400,
                detail='Password mismatch!'
            )
        return value


class UserShow(MainModel):
    id: uuid.UUID
    name: str
    surname: str
    email: EmailStr
    username: str
    is_active: bool
