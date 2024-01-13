import logging


STREAM_LOG_LEVEL = logging.INFO
FILE_LOG_LEVEL = logging.DEBUG

LOGFORMAT = "[%(levelname)s] %(asctime)s %(name)s - %(message)s (%(filename)s:%(lineno)s)"
logger_formatter = logging.Formatter(LOGFORMAT)

streamh = logging.StreamHandler()
streamh.setLevel(STREAM_LOG_LEVEL)
streamh.setFormatter(logger_formatter)

fileh = logging.FileHandler("./logger.log")
fileh.setLevel(FILE_LOG_LEVEL)
fileh.setFormatter(logger_formatter)

logger = logging.getLogger("logger")
logger.setLevel(logging.DEBUG)
logger.addHandler(fileh)
logger.addHandler(streamh)  

logger.info("asd")
