import logging
from colorlog import ColoredFormatter


STREAM_LOG_LEVEL = logging.DEBUG
FILE_LOG_LEVEL = logging.INFO
LOGFORMAT = "%(asctime)s %(name)s [%(levelname)s] - %(message)s (%(filename)s:%(lineno)s)"
DATEFORMAT = "%d-%m-%Y %H:%M:%s"
formatter = ColoredFormatter(LOGFORMAT)

stream = logging.StreamHandler()
stream.setLevel(logging.INFO)
stream.setFormatter(formatter)

fh = logging.FileHandler("./logger.log")
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)

logger = logging.getLogger("logger")
logger.setLevel(logging.DEBUG)
logger.addHandler(fh)
logger.addHandler(stream)  # Откоментирование этой строки добавляет вывод 
                             # логов в терминал
