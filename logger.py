import logging


STREAM_LOG_LEVEL = logging.INFO
FILE_LOG_LEVEL = logging.DEBUG

LOGFORMAT = "[%(levelname)s] %(asctime)s %(name)s %(filename)s:%(lineno)s %(funcName)s() - %(message)s"
logger_formatter = logging.Formatter(LOGFORMAT)

streamh = logging.StreamHandler()
streamh.setLevel(STREAM_LOG_LEVEL)
streamh.setFormatter(logger_formatter)

fileh = logging.FileHandler("./logger.log")
fileh.setLevel(FILE_LOG_LEVEL)
fileh.setFormatter(logger_formatter)

reqs_logger = logging.getLogger("reqs_logger")
reqs_logger.setLevel(logging.DEBUG)
reqs_logger.addHandler(fileh)
reqs_logger.addHandler(streamh)  

