from pydantic import BaseModel, Field, constr, conint, root_validator
from datetime import datetime

from enum import Enum

class HabitStatus(str, Enum):
    pending = "PENDING"
    done = "DONE"

class HabitBase(BaseModel):
    title: constr(min_length=1, max_length=100)
    status: HabitStatus
    category: constr(min_length=1, max_length=100)
    progress: conint(gt=0)
    goal: conint(gt=0)
    active: bool

    @root_validator(pre=True)
    def check_title_unique(cls, values):
        # Note: This validator cannot check database constraints.
        # To enforce title uniqueness, perform a DB query in the API route or service and raise ValueError if needed.
        return values


class HabitCreate(HabitBase):
    # Note: title uniqueness should be checked in the API route or service layer
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
