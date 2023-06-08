import re
from pydantic import BaseModel, EmailStr, validator, validate_email
from fastapi import HTTPException

LETTERS_PATTERN = re.compile(r"^[а-яА-Яa-zA-Z\-]+$")
EN_LOWER_LETTERS_PATTERN = re.compile(r"^[a-z0-9]+$")


class UserCreate(BaseModel):
    id: int
    name: str
    surname: str
    email: EmailStr
    username: str
    password: str

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

    @validator('username')
    def validate_username(cls, value):
        if not EN_LOWER_LETTERS_PATTERN.match(value):
            raise HTTPException(
                status_code=400,
                detail='Username should contain only latin letters in'
                       ' lower case and numbers'
            )
        return value


class UserShow(BaseModel):
    id: int
    name: str
    surname: str
    email: EmailStr
    username: str
    is_active: bool
