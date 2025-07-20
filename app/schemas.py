from pydantic import BaseModel
from datetime import datetime


class HabitBase(BaseModel):
    title: str
    status: str
    category: str
    progress: int
    goal: int
    active: bool


class HabitCreate(HabitBase):
    pass


class HabitRead(HabitBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


# New class: HabitResponse with only id, created_at, updated_at
class HabitResponse(BaseModel):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
