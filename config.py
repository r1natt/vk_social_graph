import configparser


config = configparser.ConfigParser()
config.read("config.ini")

API_KEY = config["VK_API"]["SERVICE_KEY"]

TEST_USER = config.getint("TEST", "TEST_USER")
SECOND_TEST_USER = config.getint("TEST", "SECOND_TEST_USER")