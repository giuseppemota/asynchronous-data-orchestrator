import logging
import time

from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from shared.config import settings

logger = logging.getLogger(__name__)

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def create_tables(max_attempts: int = 30, retry_interval: float = 2.0) -> None:
    from shared import models  # noqa: F401

    for attempt in range(1, max_attempts + 1):
        try:
            Base.metadata.create_all(bind=engine)
            logger.info("Database tables are ready")
            return
        except OperationalError:
            if attempt == max_attempts:
                logger.exception("Could not connect to the database")
                raise
            logger.warning(
                "Database is unavailable (attempt %s/%s); retrying in %.1f seconds",
                attempt,
                max_attempts,
                retry_interval,
            )
            time.sleep(retry_interval)
