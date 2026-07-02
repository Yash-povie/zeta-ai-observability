from .database import engine
from .models import Base

def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully")

if __name__ == "__main__":
    init_db()
