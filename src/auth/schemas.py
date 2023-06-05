from pydantic import BaseModel, EmailStr
from .models import Roles


class UserCreate(BaseModel):
    name: str
    surname: str
    email: EmailStr
    username: str
    password: str
    roles: list[Roles]
