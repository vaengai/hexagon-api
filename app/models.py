from app.database import Base
import uuid
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import JSONB


class Habit(Base):
    __tablename__ = "habits"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    status = Column(String, nullable=False)
    category = Column(String, nullable=False)
    progress = Column(Integer)
    target = Column(Integer, nullable=False)
    frequency = Column(String, nullable=False)
    active = Column(Boolean, nullable=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
    )

    user = relationship("HexagonUser", back_populates="habits")


class HexagonUser(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    email = Column(String, index=True, unique=True, nullable=False)
    full_name = Column(String, nullable=False)
    clerk_metadata = Column(JSONB, name="metadata")
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
    )
    habits = relationship("Habit", back_populates="user", cascade="all, delete-orphan")