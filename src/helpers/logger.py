import logging
import os

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    # Honor DEBUG env var: DEBUG -> DEBUG level, otherwise WARNING
    level = logging.DEBUG if os.environ.get("DEBUG") else logging.WARNING
    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
