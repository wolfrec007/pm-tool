"""Background email worker — processes the EmailOutbox on a timer."""

import asyncio
import logging
from contextlib import asynccontextmanager

from app.config import settings
from app.database import SessionLocal
from app.services.email_service import process_outbox

logger = logging.getLogger(__name__)


async def _run_worker():
    """Loop forever, processing outbox entries at the configured interval."""
    interval = settings.EMAIL_WORKER_INTERVAL_SECONDS
    logger.info(f"Email worker started (interval={interval}s, max_retries={settings.EMAIL_MAX_RETRIES})")
    while True:
        try:
            db = SessionLocal()
            try:
                result = process_outbox(db)
                if result["processed"] > 0:
                    logger.info(
                        f"Email worker: processed={result['processed']}, "
                        f"sent={result['sent']}, failed={result['failed']}"
                    )
            finally:
                db.close()
        except Exception:
            logger.exception("Email worker tick failed")
        await asyncio.sleep(interval)


@asynccontextmanager
async def email_worker_lifespan():
    """Start the email worker as a background task during app lifespan."""
    # Only start worker if SMTP is configured
    if not settings.SMTP_HOST:
        logger.info("Email worker skipped — SMTP_HOST not configured")
        yield
        return

    task = asyncio.create_task(_run_worker())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    logger.info("Email worker stopped")
