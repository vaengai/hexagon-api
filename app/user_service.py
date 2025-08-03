from sqlalchemy.orm import Session
from app.clerk_client import clerk
from models import HexagonUser
import logging

logger = logging.getLogger("hexagon")

def get_or_create_local_user(clerk_user_id: str, db: Session) -> HexagonUser:
    local_user = db.query(HexagonUser).filter_by(id=clerk_user_id).first()
    if not local_user:
        clerk_user = clerk.users.get_user(clerk_user_id)
        local_user = HexagonUser(
            id=clerk_user_id,
            email=clerk_user.email_addresses[0].email_address,
            full_name=f"{clerk_user.first_name} {clerk_user.last_name}",
            metadata=clerk_user.metadata,
        )
        db.add(local_user)
        db.commit()
        db.refresh(local_user)
        logger.info(f"Created and synced new local user {local_user.id} from Clerk")
    return local_user