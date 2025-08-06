from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Habit
from app.schemas import HabitStatus
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("hexagon")

def reset_all_habits():
    db: Session = SessionLocal()
    try:
        updated = db.query(Habit).filter(Habit.status != HabitStatus.pending.value).update(
            {Habit.status: HabitStatus.pending.value}, synchronize_session=False
        )
        db.commit()
        logger.info(f"Reset {updated} habits to 'Pending'")
    except Exception as e:
        logger.error(f"Error resetting habits: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    reset_all_habits()