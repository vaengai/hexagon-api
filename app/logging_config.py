import logging
from logging.handlers import RotatingFileHandler

logger = logging.getLogger("hexagon")

# Module-level flag to ensure configuration happens only once
_configured = False


def configure_logging():
    global _configured
    if _configured:
        return

    logger.setLevel(logging.INFO)
    logger.propagate = False  # Prevent duplicate logs from root logger
    logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)

    # File handler with error handling
    fh = None
    try:
        fh = RotatingFileHandler("hexagon.log", maxBytes=5_000_000, backupCount=3)
        fh.setLevel(logging.INFO)
        fh.setFormatter(formatter)
    except (OSError, PermissionError) as e:
        # Fall back to console-only logging in containers/restricted environments
        logger.warning(
            f"Could not create file handler: {e}. Using console logging only."
        )

    # Add handlers only if not already present
    if not logger.handlers:
        logger.addHandler(ch)
        if fh:
            logger.addHandler(fh)

    _configured = True
