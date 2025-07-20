from database import Base
import uuid
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime, timezone


class Habit(Base):
    __tablename__ = "habits"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    title = Column(String)
    status = Column(String)
    category = Column(String)
    progress = Column(Integer)
    goal = Column(Integer)
    active = Column(Boolean)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
    )
