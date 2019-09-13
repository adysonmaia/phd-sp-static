import math
import copy

INF = float("inf")
CPU = "CPU"
LINEAR_SLOPE = "a"
LINEAR_INTERCEPT = "b"
K1 = LINEAR_SLOPE
K2 = LINEAR_INTERCEPT
POWER_IDLE = "min"
POWER_MAX = "max"
BS_TYPE = "BS"


class Input:
    def __init__(self):
        self.resources = {}
        self.apps = []
        self.app_types = {}
        self.nodes = []

    def get_cloud_index(self):
        return len(self.nodes) - 1

    def get_cloud_node(self):
        return self.nodes[-1]

    def get_core_index(self):
        return len(self.nodes) - 2

    def get_core_node(self):
        return self.nodes[-2]

    def get_cpu_resource(self):
        return self.resources[CPU]

    def filter(self, app_indexes=None, node_indexes=None):
        new_input = copy.copy(self)

        if not app_indexes:
            app_indexes = range(len(self.apps))
        if not node_indexes:
            node_indexes = range(len(self.nodes))

        apps = list(map(lambda i: copy.deepcopy(self.apps[i]), app_indexes))
        nodes = list(map(lambda i: copy.deepcopy(self.nodes[i]), node_indexes))

        total_users = 0
        for app in apps:
            users = 0
            for node in nodes:
                users += app.get_users(node)
            app.nb_users = users
            total_users += users

        new_input.apps = apps
        new_input.nodes = nodes
        # new_input.nb_apps = len(apps)
        # new_input.nb_nodes = len(nodes)
        # new_input.nb_users = total_users
        return new_input


class AppType:
    def __init__(self):
        self.name = ""
        self.user_proportion = 0
        self.network = 0
        self.nb_users = 0
        self.nb_apps = 0


class App:
    def __init__(self):
        self.id = 0
        self.type = ""
        self.deadline = 0
        self.work_size = 0
        self.request_rate = 0
        self.max_instances = 0
        self.availability = 0
        self.nb_users = 0
        self.demand = {}
        self.net_delay = {}
        self.users = {}

    def get_users(self, node):
        return self.users[node.id]

    def get_demand(self, resource_name):
        value = self.demand[resource_name]
        return (value[K1], value[K2])

    def get_demand_k1(self, resource_name):
        value = self.demand[resource_name]
        return value[K1]

    def get_demand_k2(self, resource_name):
        value = self.demand[resource_name]
        return value[K2]

    def get_cpu_demand(self):
        return self.get_demand(CPU)

    def get_cpu_demand_k1(self):
        return self.get_demand_k1(CPU)

    def get_cpu_demand_k2(self):
        return self.get_demand_k2(CPU)

    def get_net_delay(self, node_i, node_j):
        return self.net_delay[node_i.id, node_j.id]

    def get_requests(self, node):
        return int(math.ceil(self.get_users(node) * self.request_rate))


class Resource:
    def __init__(self):
        self.name = ""
        self.unit = ""
        self.type = "int"
        self.precision = 4


class Node:
    def __init__(self):
        self.id = 0
        self.type = ""
        self.capacity = {}
        self.power_consumption = {}
        self.cost = {}
        self.availability = 0
        self.point = None

    def get_capacity(self, resource_name):
        return self.capacity[resource_name]

    def set_capacity(self, resource_name, value):
        self.capacity[resource_name] = value

    def get_cpu_capacity(self):
        return self.capacity[CPU]

    def get_cost(self, resource):
        value = self.cost[resource]
        return (value[K1], value[K2])

    def get_power_consumption(self):
        value = self.power_consumption
        return (value[POWER_IDLE], value[POWER_MAX])

    def is_neighbor(self, node):
        if self.point is None or node.point is None:
            return False
        else:
            return self.point.is_neighbor(node.point)

    def is_base_station(self):
        return self.type.upper() == BS_TYPE
