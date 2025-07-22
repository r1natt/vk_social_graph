import logging
import os

LOG_DIR = "./logs"

STREAM_LOG_LEVEL = logging.INFO
FILE_LOG_LEVEL = logging.DEBUG
ERROR_FILE_LOG_LEVEL = logging.ERROR

LOGFORMAT = "%(asctime)s [%(levelname)s] %(name)s:%(funcName)s():%(lineno)s - %(message)s"
formatter = logging.Formatter(LOGFORMAT)

def setup_logger():
    os.makedirs("./logs", exist_ok=True)

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # Очистим старые обработчики
    if logger.hasHandlers():
        logger.handlers.clear()

    # Консоль
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(STREAM_LOG_LEVEL)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    # Файл debug.log
    debug_handler = logging.FileHandler("./logs/debug.log")
    debug_handler.setLevel(FILE_LOG_LEVEL)
    debug_handler.setFormatter(formatter)
    logger.addHandler(debug_handler)

    # Файл error.log
    error_handler = logging.FileHandler("./logs/error.log")
    error_handler.setLevel(ERROR_FILE_LOG_LEVEL)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)

def create_logger(name, logfile, level=logging.DEBUG):
    os.makedirs(LOG_DIR, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False

    if logger.hasHandlers():
        logger.handlers.clear()

    file_handler = logging.FileHandler(os.path.join(LOG_DIR, logfile))
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(level)
    logger.addHandler(stream_handler)

    return logger