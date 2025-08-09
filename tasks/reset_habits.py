from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Habit
from app.schemas import HabitStatus
from app.logging_config import logger


def reset_all_habits():
    """Reset all habits to 'Pending' status."""
    db: Session = SessionLocal()
    try:
        logger.info("🔄 Starting habit reset process...")

        # Count total habits first
        total_habits = db.query(Habit).count()
        logger.info(f"📊 Total habits in database: {total_habits}")

        # Count habits that need resetting
        habits_to_reset = (
            db.query(Habit).filter(Habit.status != HabitStatus.pending.value).count()
        )
        logger.info(f"🎯 Habits to reset: {habits_to_reset}")

        if habits_to_reset == 0:
            logger.info("✅ No habits need resetting - all are already 'Pending'")
            return

        # Perform the reset
        updated = (
            db.query(Habit)
            .filter(Habit.status != HabitStatus.pending.value)
            .update(
                {Habit.status: HabitStatus.pending.value}, synchronize_session=False
            )
        )
        db.commit()
        logger.info(f"✅ Successfully reset {updated} habits to 'Pending'")

        # Verify the reset
        remaining_non_pending = (
            db.query(Habit).filter(Habit.status != HabitStatus.pending.value).count()
        )
        if remaining_non_pending == 0:
            logger.info("✅ All habits are now in 'Pending' status")
        else:
            logger.warning(
                f"⚠️  Still have {remaining_non_pending} non-pending habits after reset"
            )

    except Exception as e:
        logger.error(f"❌ Error resetting habits: {e}")
        logger.error(f"❌ Exception type: {type(e).__name__}")
        db.rollback()
        raise  # Re-raise the exception to make the failure visible
    finally:
        db.close()
        logger.info("🔒 Database connection closed")


if __name__ == "__main__":
    reset_all_habits()
