import logging
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
LOG_FILE = SCRIPT_DIR / "hexagon_mcp.log"

# Build a dedicated logger for this package instead of relying on basicConfig,
# which is a no-op if logging was already configured elsewhere.
logger = logging.getLogger("hexagon-mcp")
logger.setLevel(logging.INFO)
logger.propagate = False  # don't duplicate messages to root handlers

# Only add handlers once (avoids duplicates on repeated imports)
if not logger.handlers:
    # Console
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    # File (created on first write)
    try:
        fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
        fh.setLevel(logging.INFO)
    except Exception as e:
        # Fall back to console-only if file handler can't be created
        fh = None
        logging.getLogger(__name__).warning(
            f"Failed to create log file at {LOG_FILE}: {e}. Falling back to console only."
        )

    fmt = logging.Formatter(fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    if fh:
        fh.setFormatter(fmt)
        logger.addHandler(fh)

# Emit a line so the file is actually created immediately
logger.info("hexagon-mcp logging initialized at %s", LOG_FILE)
