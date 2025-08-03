from app.auth import get_current_user
from schemas import HabitRead, HabitCreate, HabitStatus
from database import Base, engine, get_db
from models import Habit, HexagonUser
from typing import List
import logging
from app.clerk_client import clerk
from fastapi import HTTPException, status, Depends, APIRouter, FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

Base.metadata.create_all(bind=engine)
from middlewares import register_middleware
from app.user_service import get_or_create_local_user
app = FastAPI(title="Habit Tracker API")
logger = logging.getLogger("hexagon")

logger.info("Starting the app...")

register_middleware(app)

router = APIRouter()

@router.get("/")
async def root():
    return {"message": "Welcome to Hexagon API"}

@router.get("/health")
async def healthcheck():
    return JSONResponse(content={"status": "ok"})

@router.post("/habit", response_model=HabitRead, status_code=status.HTTP_201_CREATED)
def create_habit(habit: HabitCreate, db: Session = Depends(get_db)):
    logger.info(f"Creating habit {habit.title}")
    existing = db.query(Habit).filter(Habit.title.ilike(habit.title.strip())).first()
    if existing:
        logger.warning(f"Habit {habit.title} already exists")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Habit with title '{habit.title}' already exists."
        )
    new_habit = Habit(**habit.dict())
    db.add(new_habit)
    db.commit()
    db.refresh(new_habit)
    logger.info(f"Created habit {habit.title} with id {new_habit.id}")
    return new_habit


# -------------------- CRUD Endpoints for Habit --------------------

@router.get("/habit", response_model=List[HabitRead])
def get_habits(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    logger.info(f"Retrieving habits {skip}/{limit}")
    return db.query(Habit).offset(skip).limit(limit).all()


@router.get("/habit/{habit_id}", response_model=HabitRead)
def get_habit(habit_id: str, db: Session = Depends(get_db)):
    logger.info(f"Retrieving habit {habit_id}")
    habit = db.query(Habit).filter(Habit.id == habit_id).first()
    if not habit:
        logger.info(f"Habit with id {habit_id} not found")
        raise HTTPException(status_code=404, detail="Habit not found")
    return habit


@router.patch("/habit/{habit_id}/status/{status}", response_model=HabitRead)
def update_status(habit_id: str, status: HabitStatus, db: Session = Depends(get_db)):
    logger.info(f"Updating status of habit {habit_id} to {status}")
    habit = db.query(Habit).filter(Habit.id == habit_id).first()
    if not habit:
        logger.info(f"Habit with id {habit_id} not found")
        raise HTTPException(status_code=404, detail="Habit not found")
    if habit.status != HabitStatus.done.value and status == HabitStatus.done:
        habit.progress = habit.progress + 1
    habit.status = status.value
    db.commit()
    db.refresh(habit)
    logger.info(f"Updated habit {habit_id} with status {status}")
    return habit

@router.patch("/habit/{id}/toggle-active", response_model=HabitRead)
def toggle_status(id: str, db: Session = Depends(get_db)):
    logger.info(f"Toggling 'active' state of habit {id}")
    habit = db.query(Habit).filter(Habit.id == id).first()
    if not habit:
        logger.info(f"Habit with id {id} not found")
        raise HTTPException(status_code=404, detail="Habit not found")
    habit.active = not habit.active
    db.commit()
    db.refresh(habit)
    logger.info(f"Toggled 'active' flag for habit {id}, now active: {habit.active}")
    return habit

@router.put("/habit/{habit_id}", response_model=HabitRead)
def update_habit(habit_id: str, habit_update: HabitCreate, db: Session = Depends(get_db)):
    logger.info(f"Updating habit {habit_id}")
    habit = db.query(Habit).filter(Habit.id == habit_id).first()
    if not habit:
        logger.info(f"Habit with id {habit_id} not found")
        raise HTTPException(status_code=404, detail="Habit not found")

    existing = db.query(Habit).filter(Habit.title.ilike(habit_update.title.strip()), Habit.id != habit_id).first()
    if existing:
        logger.warning(f"Habit with id {habit_id} already exists")
        raise HTTPException(
            status_code=400,
            detail=f"Habit with title '{habit_update.title}' already exists."
        )

    for key, value in habit_update.dict().items():
        setattr(habit, key, value)
    db.commit()
    db.refresh(habit)
    logger.info(f"Updated habit {habit_id} with id {habit_id}")
    return habit


@router.delete("/habit/{habit_id}", status_code=status.HTTP_200_OK)
def delete_habit(habit_id: str, db: Session = Depends(get_db)):
    logger.info(f"Deleting habit {habit_id}")
    habit = db.query(Habit).filter(Habit.id == habit_id).first()
    if not habit:
        logger.warning(f"Habit with id {habit_id} not found")
        raise HTTPException(status_code=404, detail="Habit not found")
    db.delete(habit)
    db.commit()
    logger.info(f"Deleted habit {habit_id}")
    return {"message": f"Habit {habit_id} deleted successfully"}

@router.get("/profile")
def get_profile(user=Depends(get_current_user), db: Session = Depends(get_db)):
    local_user = get_or_create_local_user(clerk_user_id=user["sub"], db=db)
    return {
        "local_user": {
            "id": local_user.id,
            "email": local_user.email,
            "full_name": local_user.full_name
        },
        "clerk_token_payload": user
    }

app.include_router(router)