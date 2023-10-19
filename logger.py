import logging
from colorlog import ColoredFormatter


STREAM_LOG_LEVEL = logging.DEBUG
FILE_LOG_LEVEL = logging.INFO
LOGFORMAT = "%(log_color)s%(asctime)s %(name)s [%(levelname)s] - %(message)s (%(filename)s:%(lineno)s) %(reset)s"
DATEFORMAT = "%d-%m-%Y %H:%M:%s"
formatter = ColoredFormatter(LOGFORMAT)

stream = logging.StreamHandler()
stream.setLevel(logging.DEBUG)
stream.setFormatter(formatter)

fh = logging.FileHandler("./logger.log")
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)

logger = logging.getLogger("logger")
logger.setLevel(logging.DEBUG)
logger.addHandler(fh)
logger.addHandler(stream)
