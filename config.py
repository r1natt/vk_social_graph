from dotenv import load_dotenv
import os


load_dotenv("config.env")

if not os.getenv("API_TOKEN"):
    raise EnvironmentError(f'Не заполнен апи токен. Получите апи токен и добавьте его в config.env в формате API_TOKEN="..." (https://dev.vk.com/ru/api/access-token/getting-started)')

token = os.getenv("API_TOKEN")

mongo_uri = "mongodb://localhost:27017/"
db_name = "vk_parser"
