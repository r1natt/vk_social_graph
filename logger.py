import logging


formatter = logging.Formatter(fmt=None, datefmt=None, style='%')
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
