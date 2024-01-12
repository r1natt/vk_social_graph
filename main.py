from config import my_vk_id, kate_vk_id
from pprint import pprint
import time

from reqs import get_friends, get_user_info
from db import DB
from errors import error_check, _get_vk_id_in_response


hello_text = """
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
~ Это парсер Вконтакте, призванный упростить работу по сбору информации о    ~
~ пользователях соцсети. Изначальная цель данного скрипта - составить граф   ~
~ связей определенного человека.                                             ~
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

action_text = """
Вот предлагаемый список действий:

1) Запроть информацию о конкретном пользователе
2) Составить список друзей пользователя
3) Сформировать граф друзей

Что выберите? (Введите номер действия): """


class Parser:
    def __init__(self, update=False):
        self.update = update
        print(hello_text)
        print(action_text, end="")
        self.ask()

    def ask(self):
        action = input()
        self.conds(action)

    def conds(self, action):
        match action:
            case "1":
                Users
            case "2":
                print("friends")
            case "3":
                print("graph")
            case _:
                print("Команды с таким номером нет, что выберите?: ", end="")
                self.ask()

    def get_friends_in_depth(self, vk_id, depth):
        Users([vk_id])
        friends_ids = [vk_id]
        for _ in range(2, depth + 1):
            friends_ids = Friends(friends_ids).search()
            print(friends_ids)

"""
Функционал:
 * Получить всю инфу на странице одного пользователя
 * Получить друзей пользователя
 * Сформировать граф:
    * Друзей
    * Сообществ
    * Реакций
 * Пройтись по бд
 * Пройтись по всем сохраненным до этого друзьям и обновить инфу о них
"""

#users = Users([321366596])
Parser()
#parser.get_friends_in_depth(my_vk_id, 4)
#db.update({"_id": 1}, {"$set": {"a": 2}})
