from database import Base
import uuid
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import JSONB


class Habit(Base):
    __tablename__ = "habits"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    title = Column(String)
    status = Column(String)
    category = Column(String)
    progress = Column(Integer)
    target = Column(Integer)
    frequency = Column(String)
    active = Column(Boolean)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
    )


class HexagonUser(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    email = Column(String, index=True, unique=True, nullable=False)
    full_name = Column(String, nullable=False)
    metadata = Column(JSONB)
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
    )