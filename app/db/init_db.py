import logging
from app.db.session import engine
from app.models.models import Base

logger = logging.getLogger(__name__)

def init_db():
    """
    Simpler initialization: create tables directly via SQLAlchemy.
    In production, use Alembic migrations.
    """
    try:
        logger.info("Initializing database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully.")
    except Exception as e:
        logger.error(f"Error initializing DB: {e}")
        raise

if __name__ == "__main__":
    init_db()
