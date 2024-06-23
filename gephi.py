import networkx as nx
from db import Graph
import os


class Gephi:
    def __init__(self, source):
        self.g = nx.Graph()
        self.db = Graph()
        self.source = source
        self.depth = 5
        self.social_graph()

    def save_graph(self):
        path = "./graphs"
        if not os.path.isdir(path):
            os.mkdir(path)
        filename = "./graphs/" + self.get_filename() + ".gexf"
        nx.write_gexf(self.g, filename)


    def social_graph(self):
        self.friends = self.db.get_user_friends(self.source)["friends"]
        self.fisrt_depth_friends()
        self.second_layer()
        self.filter()
        self.save_graph()
    
    def get_filename(self):
        print("Введите имя файла графа: ", end="")
        name = input()
        return name

    def fisrt_depth_friends(self):
        name = self.db  .get_name_by_vk_id(self.source)
        self.g.add_node(self.source, label=name, color="source")
        for friend in self.friends:
            name = self.db  .get_name_by_vk_id(friend)
            self.g.add_node(friend, color="red")
            self.g.add_edge(self.source, friend)

    def second_layer(self):
        for friend in self.friends:
            second_layer = self.db  .get_user_friends(friend)
            if second_layer == None:
                second_layer = []
            else:
                second_layer = second_layer["friends"]
            for i in second_layer:
                name = self.db  .get_name_by_vk_id(i)
                self.g.add_node(i, label=name)
                self.g.add_edge(friend, i)

    def filter(self):
        fedges = filter(lambda x: self.g.depth()[x[0]] < self.depth or 
                        self.g.depth()[x[1]] < self.depth, self.g.edges())
        self.g.remove_edges_from(fedges)
        fnodes = list(filter(lambda x: self.g.depth()[x] < self.depth, self.g.nodes()))
        self.g.remove_nodes_from(fnodes)

