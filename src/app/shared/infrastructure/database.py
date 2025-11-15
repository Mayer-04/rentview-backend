from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.shared.infrastructure.settings import settings


def validate_database_url() -> str:
    """Valida y retorna la URL de la base de datos."""
    db_uri = settings.database.url
    if not db_uri or not db_uri.strip():
        raise ValueError("Database URL is not configured")
    return db_uri


def _create_engine(db_uri: str) -> Engine:
    """Crea una instancia Engine lista para reutilizar en todo el proyecto."""
    return create_engine(
        db_uri,
        pool_size=settings.database.pool_size,
        max_overflow=settings.database.max_overflow,
        pool_timeout=settings.database.pool_timeout,
        pool_pre_ping=True,
        echo=settings.database.echo,
    )


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    """Retorna un Engine singleton para toda la aplicación."""
    return _create_engine(validate_database_url())


@lru_cache(maxsize=1)
def get_session_factory() -> sessionmaker[Session]:
    """Entrega una fábrica de sesiones con la configuración recomendada."""
    return sessionmaker(
        bind=get_engine(),
        class_=Session,
        autoflush=False,
        expire_on_commit=False,
    )


def open_connection_pool() -> Engine:
    engine = get_engine()

    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))

    return engine


def close_connection_pool() -> None:
    engine = get_engine()
    engine.dispose()


def get_db() -> Generator[Session]:
    session_factory = get_session_factory()
    db = session_factory()
    try:
        yield db
    finally:
        db.close()
