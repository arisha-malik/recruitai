from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

# In SQLAlchemy 2.0, we can use the DeclarativeBase class
# For backwards compatibility with standard 2.x code, declarative_base() is excellent.
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # Check connection liveness on checkout
    pool_size=10,
    max_overflow=20
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
