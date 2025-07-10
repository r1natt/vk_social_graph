from service.actions import Users, Friends
from utils.reqs import tps_bucket
from service.gephi import Gephi
from texts import texts


class Parser:
    def __init__(self, update=False):
        self.update = update
        print(texts["hello_text"])
        print(texts["action_text"], end="")
        self.ask()

    def ask(self):
        action = input()
        self.conditions(action)

    def conditions(self, action):
        match action:
            case "1":
                vk_id = int(input("Введите id пользователя: "))
                print(texts["depth_desc"])
                depth = int(input("Введите нужную глубину: "))
                Friends(vk_id, depth)
            case "2":
                vk_id = int(input("Введите id пользователя для составления графа: "))
                knees = int(input("Введите глубину: "))
                degree = int(input("Введите минимальное количество общих друзей, которые должны быть у пользователей 2-го колена: "))
                Gephi(vk_id, degree=degree, knees=knees)
            case _:
                print("Команды с таким номером нет, что выберите?: ", end="")
                self.ask()


if __name__ == "__main__":
    tps_bucket.start()
    try:
        Parser()
        tps_bucket.stop()
    except KeyboardInterrupt:
        tps_bucket.stop()

