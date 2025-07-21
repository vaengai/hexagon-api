import logging
from logging.handlers import RotatingFileHandler

logger = logging.getLogger('hexagon')

def configure_logging():
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    fh = RotatingFileHandler('hexagon.log', maxBytes=5_000_000, backupCount=3)
    fh.setFormatter(formatter)
    if not logger.handlers:
        logger.addHandler(ch)
        logger.addHandler(fh)
