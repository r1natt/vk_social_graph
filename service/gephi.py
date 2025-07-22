import networkx as nx
from typing import TypeAlias
from enum import Enum

from models._types import VK_ID, UserRecord
from .graph_search import BFS, UserTask


FILENAME: TypeAlias = str

class GraphFormat(Enum):
    GEXF = "gexf"
    GML = "gml"
    GRAPHML = "graphml"

distance_colors = {
    0: "red",       # исходный узел
    1: "orange",    # узлы на расстоянии 1
    2: "yellow",    # расстояние 2
    3: "green",     # расстояние 3
    4: "blue",      # расстояние 4
    5: "purple",    # расстояние 5
    6: "gray",      # и т.д.
}

class GexfGraph(BFS):
    def __init__(self, friend_collection, user_collection):
        super().__init__()
        self.friend_collection = friend_collection
        self.user_collection = user_collection

        self.g = nx.Graph()

    def create(self,
        vk_id: VK_ID,
        depth: int,
        degree: int=3,
        filename: str="graph",
        format: GraphFormat=GraphFormat.GEXF
    ) -> FILENAME:
        self.search(vk_id, depth)

        self.remove_low_degree_nodes(degree)

        self.save_graph(filename, format)

    def action(self, task: UserTask) -> list[VK_ID]:
        vk_id = task.vk_id
        knee = task.knee

        user_info = self.user_collection.get_by_vk_id(vk_id)

        self.new_node(user_info, knee)

        friends_record = self.friend_collection.get_by_vk_id(vk_id)
        friends_list = friends_record.active_friends

        for friend in friends_list:
            self.new_edge(vk_id, friend)

        return friends_list

    def new_node(self, user_info: UserRecord, knee: int):
        name = user_info.first_name + " " + user_info.last_name

        if knee <= max(distance_colors.keys()):
            color = distance_colors[knee]
        else:
            color = distance_colors[max(distance_colors.keys())]

        self.g.add_node(user_info.id, label=name, color=color)

    def new_edge(self, src_user, dst_user):
        self.g.add_edge(src_user, dst_user)

    def remove_low_degree_nodes(self, degree):
        to_remove = [node for node, deg in self.g.degree() if deg < degree]
        self.g.remove_nodes_from(to_remove)

    def save_graph(self, filename: str, format: GraphFormat):
        path = f"{filename}.{format.value}"

        if format == GraphFormat.GEXF:
            nx.write_gexf(self.g, path)
        elif format == GraphFormat.GML:
            nx.write_gml(self.g, path)
        elif format == GraphFormat.GRAPHML:
            nx.write_graphml(self.g, path)
        else:
            raise ValueError(f"Формат {format} не поддерживается.")

        print(f"Граф сохранён в: {path}")
