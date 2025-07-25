from models import Base
from database import engine

# ⚠️ DANGER: This drops all tables
Base.metadata.drop_all(bind=engine)

# Recreate tables
Base.metadata.create_all(bind=engine)

print("✅ Tables dropped and recreated")