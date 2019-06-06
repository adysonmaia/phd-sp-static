INF = float("inf")
CPU = "CPU"
LINEAR_SLOPE = "a"
LINEAR_INTERCEPT = "b"
K1 = LINEAR_SLOPE
K2 = LINEAR_INTERCEPT
POWER_IDLE = "min"
POWER_MAX = "max"


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

    def get_demand(self, resource):
        value = self.demand[resource]
        return (value[K1], value[K2])

    def get_demand_k1(self, resource):
        value = self.demand[resource]
        return value[K1]

    def get_demand_k2(self, resource):
        value = self.demand[resource]
        return value[K2]

    def get_cpu_demand(self):
        return self.get_demand(CPU)

    def get_cpu_demand_k1(self):
        return self.get_demand_k1(CPU)

    def get_cpu_demand_k2(self):
        return self.get_demand_k2(CPU)

    def get_net_delay(self, node_i, node_j):
        return self.net_delay[node_i.id, node_j.id]


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

    def get_capacity(self, resource):
        return self.capacity[resource]

    def set_capacity(self, resource, value):
        self.capacity[resource] = value

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
