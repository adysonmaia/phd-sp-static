import random
import math
import json
import pprint
from util import point, path

INF = float("inf")


class Input:
    def __init__(self, file):
        with open(file) as json_data:
            self.input_data = json.load(json_data)

        # pp = pprint.PrettyPrinter(indent=2)
        # pp.pprint(self.input_data)

    def gen_rand_data(self, nb_nodes, nb_apps, nb_users):
        self.nb_nodes = nb_nodes
        self.nb_apps = nb_apps
        self.nb_users = nb_users

        self._gen_rand_apps()
        self.apps_demand = [a["demand"] for a in self.apps]
        self._gen_net_graphs()
        self.net_delay = [path.calc_net_delay(g) for g in self.net_graphs]
        self._gen_nodes_capacity()
        self.resources = list(self.nodes[0].keys())
        self._gen_rand_users()

        return self.nodes, self.apps, self.users, self.resources, self.net_delay, self.apps_demand

    def _gen_rand_apps(self):
        apps_data = self.input_data["apps"]
        apps = []
        nb_app_types = len(apps_data)
        nb_apps_per_type = [self.nb_apps // nb_app_types] * nb_app_types
        nb_apps_per_type[0] += self.nb_apps % nb_app_types

        nb_users_per_type = [self.nb_users * a["users"] for a in apps_data]
        nb_users_per_type[0] += self.nb_users - sum(nb_users_per_type)

        for t in range(nb_app_types):
            data = apps_data[t]
            for i in range(nb_apps_per_type[t]):
                deadline = data["deadline"]
                if isinstance(deadline, list) or isinstance(deadline, tuple):
                    deadline = round(random.uniform(*deadline), 2)

                work_size = data["work_size"]
                if isinstance(work_size, list) or isinstance(work_size, tuple):
                    work_size = random.randrange(*work_size)

                cpu_demand_1 = work_size + 1
                cpu_demand_2 = random.randrange(int(work_size + 1))

                storage_demand_1 = data["storage"]
                storage_demand_2 = data["storage"]
                if isinstance(storage_demand_1, list) or isinstance(storage_demand_1, tuple):
                    storage_demand_1 = random.randrange(*storage_demand_1)
                    storage_demand_2 = random.randrange(*storage_demand_2)

                request_rate = data["request_rate"]
                if isinstance(request_rate, list) or isinstance(request_rate, tuple):
                    request_rate = round(random.uniform(*request_rate), 4)

                max_instances = random.randrange(1, self.nb_nodes + 1)

                users = nb_users_per_type[t] // nb_apps_per_type[t]
                if i == 0:
                    users += nb_users_per_type[t] % nb_apps_per_type[t]

                net_delay = data["net_delay"]
                app = {"deadline": deadline,
                       "max_instances": max_instances,
                       "request_rate": request_rate,
                       "work_size": work_size,
                       "users": int(users),
                       "demand": {"CPU": (cpu_demand_1, cpu_demand_2),
                                  "STORAGE": (storage_demand_1, storage_demand_2)},
                       "net_delay": net_delay}
                apps.append(app)

        self.apps = apps
        return apps

    def _gen_net_graphs(self):
        map_data = self.input_data["map"]
        nb_bs = self.nb_nodes - 2
        if map_data["format"] == "rectangle":
            rows = int(math.floor(math.sqrt(nb_bs)))
            columns = rows
            bs = point.gen_rect_map(rows, columns)
        else:
            bs = point.gen_hex_map(nb_bs)

        e_bs = list(enumerate(bs))
        core_index = self.nb_nodes - 2
        cloud_index = self.nb_nodes - 1
        r_apps = range(self.nb_apps)
        r_nodes = range(self.nb_nodes)

        graph = [[[INF for j in r_nodes]
                  for i in r_nodes] for a in r_apps]

        for a in r_apps:
            delay = self.apps[a]["net_delay"]["core_cloud"]
            if isinstance(delay, list) or isinstance(delay, tuple):
                delay = random.uniform(*delay)
            graph[a][core_index][core_index] = 0.0
            graph[a][cloud_index][cloud_index] = 0.0
            graph[a][core_index][cloud_index] = delay
            graph[a][cloud_index][core_index] = delay

        for b_index, b in e_bs:
            for a in r_apps:
                delay = self.apps[a]["net_delay"]["bs_core"]
                if isinstance(delay, list) or isinstance(delay, tuple):
                    delay = random.uniform(*delay)
                graph[a][b_index][b_index] = 0.0
                graph[a][b_index][core_index] = delay
                graph[a][core_index][b_index] = delay

            for n_index, n in e_bs:
                if b.is_neighbor(n):
                    for a in r_apps:
                        delay = self.apps[a]["net_delay"]["bs_bs"]
                        if isinstance(delay, list) or isinstance(delay, tuple):
                            delay = random.uniform(*delay)
                        graph[a][b_index][n_index] = delay
                        graph[a][n_index][b_index] = delay

        self.bs_map = bs
        self.net_graphs = graph
        return graph

    def _gen_nodes_capacity(self):
        def _get_capacity(capacity):
            result = {}
            for key, value in capacity.items():
                if isinstance(value, list) or isinstance(value, tuple):
                    value = round(random.uniform(*value), 4)
                result[key] = value
            return result

        nodes_data = self.input_data["nodes"]
        bs_capacity = nodes_data["bs"]
        core_capacity = nodes_data["core"]

        nb_bs = self.nb_nodes - 2
        capacities = [_get_capacity(bs_capacity) for _ in range(nb_bs)]
        capacities.append(_get_capacity(core_capacity))
        resources = core_capacity.keys()
        cloud_capacity = {r: INF for r in resources}
        capacities.append(cloud_capacity)

        # nb_bs = self.nb_nodes - 2
        # capacities = [bs_capacity for b in range(nb_bs)]
        # capacities.append(core_capacity)
        # resources = core_capacity.keys()
        # cloud_capacity = {r: INF for r in resources}
        # capacities.append(cloud_capacity)

        self.nodes = capacities
        return capacities

    def _gen_rand_users(self):
        nb_bs = self.nb_nodes - 2
        map_data = self.input_data["map"]
        user_distributions = map_data["distribution"]

        if map_data["format"] == "rectangle":
            bound_box = point.calc_rect_bound_box(nb_bs)
        else:
            bound_box = point.calc_hex_bound_box(nb_bs)

        r_apps = range(self.nb_apps)
        users = [[0 for _ in range(self.nb_nodes)] for _ in r_apps]
        nodes = list(enumerate(self.bs_map))
        points = []
        for a in r_apps:
            nb_users = self.apps[a]["users"]
            distribution = random.choice(user_distributions)
            if distribution == "blob":
                points = point.gen_2d_points_blob(nb_users, bound_box)
            elif distribution == "circle":
                points = point.gen_2d_points_circle(nb_users, bound_box)
            elif distribution == "moon":
                points = point.gen_2d_points_moon(nb_users, bound_box)
            else:  # uniform
                points = point.gen_2d_points_uniform(nb_users, bound_box)

            for p in points:
                # print("[{}, {}],".format(p.x, p.y))
                nodes.sort(key=lambda item: item[1].get_distance(p.to_hex()))
                index, node = nodes[0]
                users[a][index] += 1

        self.users = users
        self.users_map = points
        return users

    # def _gen_rand_users(self):
    #     r_apps = range(self.nb_apps)
    #     nb_bs = self.nb_nodes - 2
    #     users = [[0 for _ in range(self.nb_nodes)] for _ in r_apps]
    #     for a in r_apps:
    #         nb_users = self.apps[a]["users"]
    #         nodes = np.random.randint(nb_bs, size=int(nb_users))
    #         for n in nodes:
    #             users[a][n] += 1
    #
    #     self.users = users
    #     print(self.users)
    #     return users


# def print_net_graph(graph):
#     print "\n"
#     size = len(graph)
#     for i in range(size):
#         for j in range(size):
#             if(graph[i][j] == INF):
#                 print "%7s" % ("INF"),
#             else:
#                 print "%7d\t" % (graph[i][j]),
#             if j == size-1:
#                 print ""
