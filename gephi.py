import networkx as nx
from db import Graph

'''
graphdb = Graph()

G = nx.Graph()

for i in graphdb.get_all_friends():
    vk_id = i["_id"]
    friends = i["friends"]
    name = graphdb.get_name_by_vk_id(vk_id)
    color = "blue"
    G.add_node(i["_id"], label=name, color=color)
    for friend in friends:
        G.add_edge(vk_id, friend)

deg = 5
fedges = filter(lambda x: G.degree()[x[0]] < deg or G.degree()[x[1]] < deg, G.edges())
G.remove_edges_from(fedges)
fnodes = list(filter(lambda x: G.degree()[x] < deg, G.nodes()))
G.remove_nodes_from(fnodes)

nx.write_gexf(G, "artem.gexf")
'''


graphdb = Graph()

class Gephi:
    def __init__(self, source):
        self.g = nx.Graph()
        self.source = source
        self.degree = 7
        self.social_graph()


    def social_graph(self):
        self.friends = graphdb.get_user_friends(self.source)["friends"]
        self.fisrt_degree_friends()
        self.second_layer()
        self.filter()

        filename = self.get_filename() + ".gexf"
        nx.write_gexf(self.g, filename)
    
    def get_filename(self):
        print("Введите имя файла графа: ", end="")
        name = input()
        return name

    def fisrt_degree_friends(self):
        name = graphdb.get_name_by_vk_id(self.source)
        self.g.add_node(self.source, label=name, color="source")
        for friend in self.friends:
            name = graphdb.get_name_by_vk_id(friend)
            self.g.add_node(friend, color="red")
            self.g.add_edge(self.source, friend)

    def second_layer(self):
        for friend in self.friends:
            second_layer = graphdb.get_user_friends(friend)
            if second_layer == None:
                second_layer = []
            else:
                second_layer = second_layer["friends"]
            for i in second_layer:
                name = graphdb.get_name_by_vk_id(i)
                self.g.add_node(i, label=name)
                self.g.add_edge(friend, i)

    def filter(self):
        fedges = filter(lambda x: self.g.degree()[x[0]] < self.degree or 
                        self.g.degree()[x[1]] < self.degree, self.g.edges())
        self.g.remove_edges_from(fedges)
        fnodes = list(filter(lambda x: self.g.degree()[x] < self.degree, self.g.nodes()))
        self.g.remove_nodes_from(fnodes)

