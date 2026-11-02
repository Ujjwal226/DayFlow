import logging
from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class HealthService:
    @staticmethod
    def check_database_readiness(db: Session) -> bool:
        """Executes a simple SELECT 1 probe against the database."""
        try:
            result = db.execute(text("SELECT 1")).scalar()
            return result == 1
        except Exception as exc:
            logger.error("Database readiness probe failed: %s", exc)
            return False

