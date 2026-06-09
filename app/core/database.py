from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import get_config

engine = create_engine(
    get_config().DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in get_config().DATABASE_URL else {},
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


async def init_db() -> None:
    from app.models import Base
    Base.metadata.create_all(bind=engine)
    # Ensure new columns exist on existing tables (SQLite compatible)
    try:
        with engine.connect() as conn:
            from sqlalchemy import inspect, text
            inspector = inspect(conn)
            if "review_issues" in inspector.get_table_names():
                cols = {c["name"] for c in inspector.get_columns("review_issues")}
                if "resolved" not in cols:
                    conn.execute(text("ALTER TABLE review_issues ADD COLUMN resolved BOOLEAN DEFAULT 0"))
                    conn.commit()
    except Exception:
        pass


def get_db_session() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
