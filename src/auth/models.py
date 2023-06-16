import uuid
import sqlalchemy.types as types
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from enum import Enum


class Roles(str, Enum):
    role_user = 'role_user'
    role_admin = 'role_admin'
    role_superadmin = 'role_superadmin'


Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    id = Column(UUID(as_uuid=True),
                primary_key=True,
                default=uuid.uuid4)
    username = Column(String,
                      nullable=False,
                      unique=True)
    email = Column(String,
                   nullable=False,
                   unique=True)
    name = Column(String, nullable=False)
    surname = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    roles = Column(ARRAY(String), nullable=False)

    def __repr__(self):
        return f'User: {self.username}'

    @property
    def is_superadmin(self) -> bool:
        return Roles.role_superadmin in self.roles

    @property
    def is_admin(self) -> bool:
        return Roles.role_admin in self.roles


class TokenChoicesTypes(types.TypeDecorator):
    impl = types.String

    def __init__(self, choices, **kw):
        self.choices = dict(choices)
        super().__init__(**kw)

    def process_bind_param(self, value, dialect):
        return [k for k, v in self.choices.items() if v == value][0]


class AuthToken(Base):
    TOKEN_TYPES = {
        'su': 'su',
        'ce': 'ce',
        'pr': 'pr'
    }
    __tablename__ = 'auth_tokens'

    id = Column(UUID(as_uuid=True),
                primary_key=True,
                default=uuid.uuid4)
    token = Column(String(length=32),
                   unique=True,
                   nullable=False)
    token_type = Column(TokenChoicesTypes(TOKEN_TYPES), nullable=False)
    token_owner = Column(String(length=150), nullable=False)
    created = Column(DateTime(timezone=True), server_default=func.now())
    expired = Column(Boolean, default=False)

    def __repr__(self):
        return f'TOKEN: {self.token}, OWNER: {self.token_owner}'
