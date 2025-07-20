from schemas import HabitRead, HabitCreate
from database import Base, engine, get_db
from fastapi import FastAPI
from models import Habit
from fastapi_crudrouter import SQLAlchemyCRUDRouter

Base.metadata.create_all(bind=engine)
app = FastAPI(title="Habit Tracker API")

habit_router= SQLAlchemyCRUDRouter(
    schema=HabitRead,
    create_schema=HabitCreate,
    db_model=Habit,
    db = get_db,
    prefix="habit",
)

app.include_router(habit_router)