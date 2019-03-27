import random
import math
import json
from util import point, path, model

INF = float("inf")


def get_int_param(param):
    if isinstance(param, list) or isinstance(param, tuple):
        param = random.randrange(*param)
    if param == "INF":
        param = INF
    else:
        param = int(param)
    return param


def get_float_param(param, precision=None):
    if isinstance(param, list) or isinstance(param, tuple):
        param = random.uniform(*param)
    if param == "INF":
        param = INF
    else:
        param = float(param)
    if precision is not None:
        param = round(param, precision)
    return param


class Input:
    def __init__(self, file):
        with open(file) as json_data:
            self.input_data = json.load(json_data)

    def get_cloud_index(self):
        return len(self.nodes) - 1

    def get_core_index(self):
        return len(self.nodes) - 2

    def get_cpu_resource(self):
        return self.resources["CPU"]

    def gen_rand_data(self, nb_nodes, nb_apps, nb_users):
        self.nb_nodes = nb_nodes
        self.nb_apps = nb_apps
        self.nb_users = nb_users

        self._gen_resources()
        self._gen_apps()
        self._gen_nodes()
        self._gen_network()
        self._gen_users()

        return self

    def _gen_resources(self):
        data = self.input_data["resources"]
        self.resources = {}

        for r in data:
            resouce = model.Resource()
            key = r["name"]
            resouce.name = key
            resouce.unit = r["unit"]
            if "type" in r:
                resouce.type = r["type"]
            if "precision" in r:
                resouce.precision = int(r["precision"])

            self.resources[key] = resouce

        return self

    def _gen_apps(self):
        data = self.input_data["apps"]
        nb_types = len(data)

        type_nb_apps = [self.nb_apps // nb_types] * nb_types
        type_nb_apps[0] += self.nb_apps % nb_types

        type_nb_users = [int(math.floor(self.nb_users * a["users"])) for a in data]
        type_nb_users[0] += self.nb_users - sum(type_nb_users)

        app_id = 0
        self.apps = []
        self.app_types = {}
        for type_index in range(nb_types):
            type_data = data[type_index]

            type = model.AppType()
            type.nb_apps = type_nb_apps[type_index]
            type.nb_users = type_nb_users[type_index]
            type.name = type_data["type"]
            type.user_proportion = type_data["users"]
            type.network = type_data["network_delay"]
            self.app_types[type.name] = type

            if type.nb_apps <= 0 or type.nb_users <= 0:
                continue

            app_nb_users = [type.nb_users // type.nb_apps] * type.nb_apps
            app_nb_users[0] += type.nb_users % type.nb_apps

            for app_index in range(type.nb_apps):
                app = self._gen_app(type_data)
                app.id = app_id
                app.nb_users = app_nb_users[app_index]
                self.apps.append(app)

                app_id += 1

        return self

    def _gen_app(self, data):
        app = model.App()

        app.type = data["type"]
        app.deadline = get_float_param(data["deadline"], 4)
        app.work_size = get_int_param(data["work_size"])
        app.request_rate = get_float_param(data["request_rate"], 4)

        max_instances = 0
        if "max_instances" in data:
            percentage = get_float_param(data["max_instances"])
            max_instances = int(round(percentage * self.nb_nodes))
            max_instances = max(1, max_instances)
        else:
            max_instances = random.randint(1, self.nb_nodes)
        app.max_instances = max_instances

        # TODO: improve CPU demand based on WORK SIZE
        app.demand = {}
        for r_name, r in self.resources.items():
            r_demand = {"a": 0, "b": 0}

            if r_name == "CPU":
                r_demand["a"] = app.work_size
                r_demand["b"] = round(app.work_size / app.deadline) + 1

            if r_name in data["demand"]:
                r_data = data["demand"][r_name]
                for key in r_demand.keys():
                    if key not in r_data:
                        continue

                    value = r_data[key]
                    if r.type == "int":
                        value = get_int_param(value)
                    elif r.type == "float":
                        value = get_float_param(value, r.precision)
                    r_demand[key] = value

            app.demand[r.name] = r_demand

        return app

    def _gen_nodes(self):
        map_data = self.input_data["map"]
        nb_bs = self.nb_nodes - 2

        bs_points = []
        if map_data["format"] == "rectangle":
            rows = int(math.floor(math.sqrt(nb_bs)))
            columns = rows
            bs_points = point.gen_hex_rect_map(rows, columns)
        else:
            bs_points = point.gen_hex_map(nb_bs)

        node_id = 0
        self.nodes = []

        bs_data = self.input_data["nodes"]["BS"]
        for bs_index in range(nb_bs):
            node = self._gen_node(bs_data)
            node.id = node_id
            node.point = bs_points[bs_index]
            self.nodes.append(node)
            node_id += 1

        types = ["CORE", "CLOUD"]
        for type in types:
            node = self._gen_node(self.input_data["nodes"][type])
            node.id = node_id
            self.nodes.append(node)
            node_id += 1

        return self

    def _gen_node(self, data):
        node = model.Node()
        node.type = data["type"]

        power = {"min": 0, "max": 0}
        for key in power:
            power[key] = get_float_param(data["power"][key], 2)
        node.power_consumption = power

        node.cost = {}
        node.capacity = {}
        for r_name, r in self.resources.items():
            r_cost = {"a": 0, "b": 0}
            r_capacity = 0

            if r_name in data["cost"]:
                r_data = data["cost"][r_name]
                for key in r_cost.keys():
                    if key not in r_data:
                        continue
                    r_cost[key] = get_float_param(r_data[key])

            if r_name in data["capacity"]:
                r_capacity = data["capacity"][r_name]
                if r.type == "int":
                    r_capacity = get_int_param(r_capacity)
                elif r.type == "float":
                    r_capacity = get_float_param(r_capacity, r.precision)

            node.cost[r.name] = r_cost
            node.capacity[r.name] = r_capacity

        return node

    def _gen_network(self):
        nb_nodes = len(self.nodes)
        r_nodes = range(nb_nodes)

        for app in self.apps:
            app_type = self.app_types[app.type]
            net_data = app_type.network

            graph = [[INF for j in r_nodes] for i in r_nodes]
            for i in r_nodes:
                node_i = self.nodes[i]
                for j in range(i, nb_nodes):
                    node_j = self.nodes[j]
                    delay = INF

                    if i == j:
                        delay = 0
                    elif node_i.type != node_j.type or node_i.is_neighbor(node_j):
                        key_1 = node_i.type + "_" + node_j.type
                        key_2 = node_j.type + "_" + node_i.type
                        if key_1 in net_data:
                            delay = get_float_param(net_data[key_1])
                        elif key_2 in net_data:
                            delay = get_float_param(net_data[key_2])

                    graph[i][j] = delay
                    graph[j][i] = delay

            shortest_delay = path.calc_net_delay(graph)
            app.net_delay = {}
            for i in r_nodes:
                id_i = self.nodes[i].id
                for j in r_nodes:
                    id_j = self.nodes[j].id
                    delay = round(shortest_delay[i][j], 4)
                    app.net_delay[(id_i, id_j)] = delay

        return self

    def _gen_users(self):
        nb_bs = self.nb_nodes - 2
        map_format = self.input_data["map"]['format']
        distributions = self.input_data["map"]["distribution"]

        bound_box = None
        if map_format == "rectangle":
            bound_box = point.calc_rect_bound_box(nb_bs)
        else:
            bound_box = point.calc_hex_bound_box(nb_bs)

        bs_nodes = list(filter(lambda n: n.type == "BS", self.nodes))
        for app in self.apps:
            points = self._gen_points(app.nb_users, distributions, bound_box)
            app.users = {n.id: 0 for n in self.nodes}
            for p in points:
                min_dist = INF
                min_bs = None
                for bs in bs_nodes:
                    dist = INF
                    if bs.point is not None:
                        dist = p.get_distance(bs.point)
                    if dist < min_dist:
                        min_dist = dist
                        min_bs = bs

                app.users[min_bs.id] += 1

    def _gen_points(self, nb_points, distributions, bound_box):
        distribution = random.choice(distributions)
        if distribution == "blob":
            points = point.gen_2d_points_blob(nb_points, bound_box)
        elif distribution == "circle":
            points = point.gen_2d_points_circle(nb_points, bound_box)
        elif distribution == "moon":
            points = point.gen_2d_points_moon(nb_points, bound_box)
        else:  # uniform
            points = point.gen_2d_points_uniform(nb_points, bound_box)

        return points
