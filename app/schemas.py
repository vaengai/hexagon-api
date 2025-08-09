from pydantic import BaseModel, Field
from datetime import datetime

from enum import Enum


class HabitStatus(str, Enum):
    pending = "Pending"
    done = "Done"


class HabitFrequency(str, Enum):
    daily = "Day"
    weekly = "Week"
    monthly = "Month"


class HabitBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    status: HabitStatus
    category: str = Field(..., min_length=1, max_length=100)
    progress: int
    target: int = Field(..., gt=0)
    frequency: HabitFrequency
    active: bool


class HabitCreate(HabitBase):
    # Note: title uniqueness should be checked in the API route or service layer
    pass


class HabitRead(HabitBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


# New class: HabitResponse with only id, created_at, updated_at
class HabitResponse(BaseModel):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
