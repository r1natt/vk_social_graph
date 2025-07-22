import configparser
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config.ini"

config = configparser.ConfigParser()
config.read(CONFIG_PATH)

API_KEY = config["VK_API"]["SERVICE_KEY"]

MONGO_URI = config["MONGO"]["URI"]
MONGO_DB_NAME = config["MONGO"]["DB_NAME"]
MONGO_TEST_DB_NAME = config["MONGO_TEST"]["DB_NAME"]

TEST_USER = config.getint("TEST", "TEST_USER")
SECOND_TEST_USER = config.getint("TEST", "SECOND_TEST_USER")