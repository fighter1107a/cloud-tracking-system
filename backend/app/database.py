from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.app.config import settings

# Handle SQLite vs PostgreSQL engine arguments
connect_args = {}
db_url = settings.DATABASE_URL

if db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
elif db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+psycopg2://", 1)
elif db_url.startswith("postgresql://") and not db_url.startswith("postgresql+"):
    # SQLAlchemy 2 defaults postgresql:// to psycopg (v3). If psycopg2 is installed, map to psycopg2.
    try:
        import psycopg2
        db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)
    except ImportError:
        pass

engine = create_engine(
    db_url,
    connect_args=connect_args,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """Dependency to provide a database session per request with proper cleanup."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
