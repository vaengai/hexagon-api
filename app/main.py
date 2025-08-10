import os
from contextlib import asynccontextmanager
from typing import List
from app.logging_config import logger
from fastapi import HTTPException, status, Depends, APIRouter, FastAPI
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from app.auth_secure import get_current_user
from app.database import Base, engine, get_db
from app.models import Habit
from app.schemas import HabitRead, HabitCreate, HabitStatus
from datetime import datetime, timedelta

from app.middlewares import register_middleware
from app.user_service import get_or_create_local_user


from apscheduler.schedulers.background import BackgroundScheduler
from tasks.reset_habits import reset_all_habits

Base.metadata.create_all(bind=engine)
scheduler = BackgroundScheduler()

logger.info("Starting the app...")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Context manager for FastAPI application lifespan events.
    Handles starting and stopping the APScheduler for background tasks such as resetting all habits daily.
    """
    try:
        scheduler.add_job(
            reset_all_habits, "cron", hour=0, minute=0, id="reset_habits_daily"
        )
        scheduler.start()
        logger.info(
            "✅ APScheduler started and scheduled reset_all_habits for midnight UTC daily."
        )

        # Run once immediately for testing if enabled via environment variable

        if os.getenv("RUN_INITIAL_RESET", "false").lower() == "true":
            logger.info(
                "🔄 Running reset_all_habits immediately for verification (RUN_INITIAL_RESET enabled)..."
            )
            try:
                reset_all_habits()
                logger.info("✅ Initial reset_all_habits completed successfully.")
            except Exception as e:
                logger.error(f"❌ Initial reset_all_habits failed: {e}")
        yield
    finally:
        if scheduler.running:
            scheduler.shutdown()
            logger.info("🛑 APScheduler shut down.")


app = FastAPI(title="Habit Tracker API", lifespan=lifespan)


register_middleware(app)


router = APIRouter()
security = HTTPBearer()


@router.get("/")
async def root():
    return {"message": "Welcome to Hexagon API"}


@router.get("/health")
async def healthcheck():
    return JSONResponse(content={"status": "ok"})


@router.get("/scheduler-status")
async def scheduler_status():
    """Check the status of the background scheduler and jobs."""
    try:
        is_running = scheduler.running
        jobs = []
        for job in scheduler.get_jobs():
            jobs.append(
                {
                    "id": job.id,
                    "name": job.name,
                    "next_run_time": (
                        str(job.next_run_time) if job.next_run_time else None
                    ),
                    "trigger": str(job.trigger),
                }
            )

        return {"scheduler_running": is_running, "total_jobs": len(jobs), "jobs": jobs}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to get scheduler status: {str(e)}"},
        )


@router.post("/habit", response_model=HabitRead, status_code=status.HTTP_201_CREATED)
def create_habit(
    habit: HabitCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
    token=Depends(security),
):
    logger.info(f"Creating habit {habit.title}")
    existing = db.query(Habit).filter(Habit.title.ilike(habit.title.strip())).first()
    if existing:
        logger.warning(f"Habit {habit.title} already exists")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Habit with title '{habit.title}' already exists.",
        )
    local_user = get_or_create_local_user(clerk_user_id=user["sub"], db=db)

    new_habit = Habit(**habit.dict(), user_id=local_user.id)
    db.add(new_habit)
    db.commit()
    db.refresh(new_habit)
    logger.info(f"Created habit {habit.title} with id {new_habit.id}")
    return new_habit


# -------------------- CRUD Endpoints for Habit --------------------


@router.get("/habit", response_model=List[HabitRead])
def get_habits(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
    token=Depends(security),
):
    logger.info(f"Retrieving habits {skip}/{limit}")
    local_user = get_or_create_local_user(clerk_user_id=user["sub"], db=db)

    return (
        db.query(Habit)
        .filter(Habit.user_id == local_user.id)
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/habit/{habit_id}", response_model=HabitRead)
def get_habit(
    habit_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
    token=Depends(security),
):
    logger.info(f"Retrieving habit {habit_id}")
    local_user = get_or_create_local_user(clerk_user_id=user["sub"], db=db)

    habit = (
        db.query(Habit)
        .filter(Habit.id == habit_id, Habit.user_id == local_user.id)
        .first()
    )
    if not habit:
        logger.info(f"Habit with id {habit_id} not found")
        raise HTTPException(status_code=404, detail="Habit not found")
    return habit


@router.patch("/habit/{habit_id}/status/{status}", response_model=HabitRead)
def update_status(
    habit_id: str,
    status: HabitStatus,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
    token=Depends(security),
):
    logger.info(f"Updating status of habit {habit_id} to {status}")
    local_user = get_or_create_local_user(clerk_user_id=user["sub"], db=db)

    habit = (
        db.query(Habit)
        .filter(Habit.id == habit_id, Habit.user_id == local_user.id)
        .first()
    )
    if not habit:
        logger.info(f"Habit with id {habit_id} not found")
        raise HTTPException(status_code=404, detail="Habit not found")

    # Store previous status for comparison
    previous_status = habit.status
    current_progress = habit.progress or 0

    # Handle progress increment/decrement logic
    if (
        previous_status != HabitStatus.done.value
        and status.value == HabitStatus.done.value
    ):
        # Moving from not-done to done: increment progress
        habit.progress = current_progress + 1
        logger.info(f"Incremented progress for habit {habit_id}: {habit.progress}")
    elif (
        previous_status == HabitStatus.done.value
        and status.value != HabitStatus.done.value
    ):
        # Moving from done to not-done: decrement progress (with minimum of 0)
        habit.progress = max(0, current_progress - 1)
        logger.info(f"Decremented progress for habit {habit_id}: {habit.progress}")

    # Validate status transition
    if status.value == HabitStatus.done.value and not habit.active:
        logger.warning(f"Attempting to mark inactive habit {habit_id} as done")
        raise HTTPException(
            status_code=400, detail="Cannot mark inactive habit as done"
        )

    # Update the status
    habit.status = status.value
    db.commit()
    db.refresh(habit)

    logger.info(f"Updated habit {habit_id} from {previous_status} to {status.value}")
    return habit


@router.patch("/habit/{id}/toggle-active", response_model=HabitRead)
def toggle_status(
    id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
    token=Depends(security),
):
    logger.info(f"Toggling 'active' state of habit {id}")
    local_user = get_or_create_local_user(clerk_user_id=user["sub"], db=db)

    habit = (
        db.query(Habit).filter(Habit.id == id, Habit.user_id == local_user.id).first()
    )
    if not habit:
        logger.info(f"Habit with id {id} not found")
        raise HTTPException(status_code=404, detail="Habit not found")
    setattr(habit, "active", not getattr(habit, "active"))
    db.commit()
    db.refresh(habit)
    logger.info(f"Toggled 'active' flag for habit {id}, now active: {habit.active}")
    return habit


@router.put("/habit/{habit_id}", response_model=HabitRead)
def update_habit(
    habit_id: str,
    habit_update: HabitCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
    token=Depends(security),
):
    local_user = get_or_create_local_user(clerk_user_id=user["sub"], db=db)
    habit = (
        db.query(Habit)
        .filter(Habit.id == habit_id, Habit.user_id == local_user.id)
        .first()
    )
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")

    existing = (
        db.query(Habit)
        .filter(
            Habit.title.ilike(habit_update.title.strip()),
            Habit.id != habit_id,
            Habit.user_id == local_user.id,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Habit with title '{habit_update.title}' already exists.",
        )

    for key, value in habit_update.dict().items():
        setattr(habit, key, value)

    db.commit()
    db.refresh(habit)
    return habit


@router.delete("/habit/{habit_id}", status_code=status.HTTP_200_OK)
def delete_habit(
    habit_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
    token=Depends(security),
):
    local_user = get_or_create_local_user(clerk_user_id=user["sub"], db=db)
    habit = (
        db.query(Habit)
        .filter(Habit.id == habit_id, Habit.user_id == local_user.id)
        .first()
    )
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")

    db.delete(habit)
    db.commit()
    return {"message": f"Habit {habit_id} deleted successfully"}


@router.get("/profile")
def get_profile(
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
    token=Depends(security),
):
    local_user = get_or_create_local_user(clerk_user_id=user["sub"], db=db)
    return {
        "local_user": {
            "id": local_user.id,
            "email": local_user.email,
            "full_name": local_user.full_name,
        },
        "clerk_token_payload": user,
    }


@router.post("/admin/reset-habits")
def manual_reset_habits(user=Depends(get_current_user), token=Depends(security)):
    """Manual endpoint to trigger habit reset - useful for testing and debugging."""
    try:
        logger.info(
            f"Manual habit reset triggered by user: {user.get('sub', 'unknown')}"
        )
        reset_all_habits()
        return {"message": "Habits reset successfully", "status": "success"}
    except Exception as e:
        logger.error(f"Manual habit reset failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset habits: {str(e)}",
        )


@router.get("/bulk/habits/{num_days}")
def fetch_last_x_days_habits(
    num_days: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
    token=Depends(security),
):
    logger.info(f"Bulk Retrieving habits for {num_days}")
    local_user = get_or_create_local_user(clerk_user_id=user["sub"], db=db)

    cutoff_date = datetime.now() - timedelta(days=num_days)

    habits = (
        db.query(Habit)
        .filter(Habit.user_id == local_user.id)
        .filter(Habit.created_at > cutoff_date)
        .all()
    )

    # Group habits by date
    habits_by_date = {}
    for habit in habits:
        date_key = habit.created_at.date().isoformat()
        if date_key not in habits_by_date:
            habits_by_date[date_key] = []
        habits_by_date[date_key].append(habit)

    return habits_by_date


app.include_router(router)
