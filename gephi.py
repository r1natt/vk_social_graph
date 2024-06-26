import networkx as nx
from db import Graph
import os


class Gephi:
    def __init__(self, source, degree=7, knees=2):
        self.g = nx.Graph()
        self.db = Graph()
        self.source = source
        self.degree = degree
        self.knees = knees

        self.all_users_in_g = set()
        self.last_layer = set()
        self.new_layer = set()
        """
        last_layer, new_layer нужны для графов, в которых нужно спускаться до 
            3-го колена и ниже
        Например я заполняю пользователей n-го колена и для заполнения n-го 
            колена я беру пользователей, которые уже есть на графе из n-1-го 
            колена (из last_layer)
            А для заполнения следующего колена я добавляю пользователей n-го 
            колена в new_layer, который на следующей иттерации ставится last_layer 
            и так далее   
        """
        
        self.social_graph()

    def social_graph(self):
        self.get_source_users_data()
        self.layer_manager()
        self.save_graph()

    def get_source_users_data(self):
        name = self.db.get_name_by_vk_id(self.source)
        self.g.add_node(self.source, label=name, color="source")

        friends = set(self.db.get_user_friends(self.source)["friends"])
        self.last_layer = friends
        self.all_users_in_g = self.all_users_in_g.union(self.last_layer)
        for friend in friends:
            name = self.db.get_name_by_vk_id(friend)
            self.g.add_node(friend, label=name, color="1_knee")
            self.g.add_edge(self.source, friend)
        
    def layer_manager(self):
        for i in range(self.knees - 1):
            self.add_layer(i + 2)
            self.last_layer = self.new_layer
            self.all_users_in_g = self.all_users_in_g.union(self.last_layer)
            self.new_layer = set()

    def add_to_g_ques(self, vk_id):
        count_of_mut_rels = self.db.get_count_of_mutual_relations(self.all_users_in_g, vk_id)
        if count_of_mut_rels >= self.degree:
            return True
        return False

    def is_node_in_g(self, vk_id):
        if vk_id in self.g.nodes:
            return True
        return False

    def is_edge_in_g(self, source, target):
        var1 = (source, target)
        var2 = (target, source)
        if var1 in self.g.edges:
            return True
        if var2 in self.g.edges:
            return True
        return False

    def add_layer(self, n_layer):
        for n, user_from_last_layer in enumerate(self.last_layer):
            print(f"{n_layer} колено: {n + 1} / {len(self.last_layer)}\r", end="")

            users_friends = self.db.get_user_friends(user_from_last_layer)["friends"]

            for k, users_friend in enumerate(users_friends):
                if self.add_to_g_ques(users_friend):
                    self.add_layer_user(user_from_last_layer, users_friend, f"{n_layer}_knee")
        print(f"{n_layer} колено сохранено")

    def add_layer_user(self, source, target, color_label):
        if not self.is_node_in_g(target):
            self.new_layer.add(target)
            """
            Добавляю в пользователей нынешего слоя только пользователей, 
            которых до этого не было на графе
            """
            name = self.db.get_name_by_vk_id(target)
            self.g.add_node(target, label=name, color=color_label)
        if not self.is_edge_in_g(source, target):
            self.g.add_edge(source, target)

    def save_graph(self):
        path = "./graphs"
        if not os.path.isdir(path):
            os.mkdir(path)
        filename = self.get_filename()
        file_path = "./graphs/" + filename + ".gexf"
        nx.write_gexf(self.g, file_path)
        print(f"Файл сохранен в ./graphs/{filename}.gexf")
    
    def get_filename(self):
        print("Введите имя файла графа: ", end="")
        name = input()
        return name
            
