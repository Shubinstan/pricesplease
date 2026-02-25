# src/api/dependencies.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.core.config import settings

# Create a connection engine (pool_pre_ping checks whether the database is alive before making a request)
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

# Session Factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """
    Dependency, которая выдает сессию БД для каждого запроса (Request).
    Использование yield гарантирует закрытие сессии даже при ошибках.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()