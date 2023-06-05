import uuid
from src.config import Base
from sqlalchemy import Column, String, Boolean
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from enum import Enum


class Roles(str, Enum):
    role_user = 'role_user'
    role_admin = 'role_admin'
    role_superadmin = 'role_superadmin'


class User(Base):
    __tablename__ = 'users'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, nullable=False, unique=True)
    email = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)
    surname = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    roles = Column(ARRAY(String), nullable=False)

    @property
    def is_superadmin(self) -> bool:
        return Roles.role_superadmin in self.roles

    @property
    def is_admin(self) -> bool:
        return Roles.role_admin in self.roles
