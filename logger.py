import logging


STREAM_LOG_LEVEL = logging.INFO
FILE_LOG_LEVEL = logging.DEBUG

LOGFORMAT = "[%(levelname)s] %(asctime)s %(name)s %(filename)s:%(lineno)s %(funcName)s() - %(message)s"
logger_formatter = logging.Formatter(LOGFORMAT)

streamh = logging.StreamHandler()
streamh.setLevel(STREAM_LOG_LEVEL)
streamh.setFormatter(logger_formatter)

fileh = logging.FileHandler("./logs/general.log")
fileh.setLevel(FILE_LOG_LEVEL)
fileh.setFormatter(logger_formatter)

reqs_file = logging.FileHandler("./logs/reqs.log")
reqs_file.setLevel(FILE_LOG_LEVEL)
reqs_file.setFormatter(logger_formatter)

general_log = logging.getLogger("general")
general_log.setLevel(logging.DEBUG)
general_log.addHandler(fileh)
general_log.addHandler(streamh)  

reqs_log = logging.getLogger("reqs")
reqs_log.setLevel(logging.DEBUG)
reqs_log.addHandler(reqs_file)
