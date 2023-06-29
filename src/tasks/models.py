import uuid

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, ForeignKey, String, Boolean, DateTime, Integer, Date, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from src.auth.models import User

from src.database.core import Base


# Base = declarative_base()


class Tasks(Base):
    __tablename__ = 'tasks'

    id = Column(UUID(as_uuid=True),  # as_uuid helps us to return python uuid
                primary_key=True,
                default=uuid.uuid4)
    creator_id = Column(UUID(as_uuid=True), ForeignKey(User.id))
    creator = relationship(lambda: User, back_populates='tasks')
    title = Column(String(length=150), nullable=False)
    task_text = Column(Text, nullable=False)
    created = Column(DateTime(timezone=True), server_default=func.now())
    updated = Column(DateTime(timezone=True), nullable=True)
    deadline = Column(Date, nullable=False)
    expired = Column(Boolean, default=False)

    def __repr__(self):
        return f'Task: {self.title}, creator: {self.creator.username}'
