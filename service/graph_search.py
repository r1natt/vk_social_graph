from dataclasses import dataclass
import logging
from queue import PriorityQueue
from abc import ABC, abstractmethod

from models._types import VK_ID


logger = logging.getLogger(__name__)


@dataclass(order=True)
class UserTask:
    knee: int
    vk_id: int


class GraphSearch(ABC):
    @abstractmethod
    def search(self, vk_id: VK_ID, max_depth: int):
        pass


class BFS(GraphSearch):
    def __init__(self):
        self.queue = PriorityQueue()
        self.visited = set()

    def search(self, vk_id: VK_ID, max_depth: int):
        self._start_point(vk_id)

        while not self.queue.empty():
            task = self.queue.get()
            vk_id = task.vk_id
            knee = task.knee

            if knee > max_depth:
                # Точка выхода из цикла. Важно чтобы очередь была приоритетной
                break

            if self._is_visited(vk_id):
                continue

            childs_list = self.action(task)
            # В моем случае childs - друзья пользователя, такое имя написано в
            # псевдокоде википедии

            for friend_vk_id in childs_list:
                if knee + 1 <= max_depth:
                    self.queue.put(
                        UserTask(
                            knee=knee + 1,
                            vk_id=friend_vk_id
                        )
                    )

            self.visited.add(vk_id)
            print(len(self.visited))

    def _is_visited(self, vk_id: VK_ID):
        return vk_id in self.visited

    def _start_point(self, vk_id: VK_ID):
        task = UserTask(knee=0, vk_id=vk_id)
        self.queue.put(task)

    @abstractmethod
    def action(self, task: UserTask) -> list[VK_ID]:
        """
        Этот метод может выполнять любые промежуточные действия, но должен
        вернуть список друзей пользователя vk_id.

        В реализации парсера этот метод будет вызывать методы get_user(vk_id) и
        вызывать и возвращать get_friends(vk_id).

        В реализации графа этот метод будет добавлять из бд информацию о
        пользователе в граф и возвращать информацию о друзьях пользователя.

        Такая реализация теряет Single Responsibility, но позволяет
        переиспользовать BFS, метод которого не меняется в зависимости от цели
        """
        pass
