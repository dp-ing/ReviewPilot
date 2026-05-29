from collections.abc import Generator

from sqlalchemy.orm import Session

from app.core.database import get_db_session, engine, SessionLocal


class TestDatabaseEngine:
    def test_engine_is_created(self) -> None:
        assert engine is not None
        assert "sqlite" in str(engine.url)

    def test_session_local_is_configured(self) -> None:
        assert SessionLocal is not None
        session = SessionLocal()
        assert isinstance(session, Session)
        session.close()


class TestGetDbSession:
    def test_returns_generator(self) -> None:
        gen = get_db_session()
        assert isinstance(gen, Generator)

    def test_yields_valid_session(self) -> None:
        gen = get_db_session()
        session = next(gen)
        try:
            assert isinstance(session, Session)
        finally:
            try:
                next(gen)
            except StopIteration:
                pass
