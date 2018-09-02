from collections import namedtuple
import numpy as np
import random
import math

INF = float("inf")
HexPoint = namedtuple('HexPoint', ['q', 'r'])

CLOUD_DELAY_INDEX = "core_cloud"
CORE_DELAY_INDEX = "bs_core"
BS_DELAY_INDEX = "bs_bs"


def get_hex_neighbors(point):
    # https://www.redblobgames.com/grids/hexagons/#neighbors-axial
    directions = [(1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1)]
    neighbors = [HexPoint(point.q + d[0], point.r + d[1])
                 for d in directions]
    return neighbors


def gen_hex_map(nb_points):
    # https://www.redblobgames.com/grids/hexagons/#range
    delta_sqrt = math.sqrt(9 + 12*(nb_points - 1))
    if delta_sqrt > 3:
        size = (3 + delta_sqrt) / 6.0
    else:
        size = (3 - delta_sqrt) / 6.0
    size = int(math.floor(size))

    points = []
    count = 0
    for q in range(-size, size + 1):
        for r in range(max(-size, -size-q), min(size, size-q) + 1):
            if count < nb_points:
                points.append(HexPoint(q, r))
                count += 1
    return points


def gen_net_graphs(nb_nodes, app_link_delay):
    bs = gen_hex_map(nb_nodes - 2)
    e_bs = list(enumerate(bs))
    bs_indexes = {b: i for i, b in e_bs}
    core_index = nb_nodes - 2
    cloud_index = nb_nodes - 1
    nb_apps = len(app_link_delay)
    r_apps = range(nb_apps)

    graph = [[[INF for j in range(nb_nodes)]
              for i in range(nb_nodes)] for a in r_apps]

    for a in r_apps:
        delay = app_link_delay[a][CLOUD_DELAY_INDEX]
        if isinstance(delay, list) or isinstance(delay, tuple):
            delay = random.uniform(*delay)
        graph[a][core_index][core_index] = 0.0
        graph[a][cloud_index][cloud_index] = 0.0
        graph[a][core_index][cloud_index] = delay
        graph[a][cloud_index][core_index] = delay

    for b_index, b in e_bs:
        for a in r_apps:
            delay = app_link_delay[a][CORE_DELAY_INDEX]
            if isinstance(delay, list) or isinstance(delay, tuple):
                delay = random.uniform(*delay)
            graph[a][b_index][b_index] = 0.0
            graph[a][b_index][core_index] = delay
            graph[a][core_index][b_index] = delay

        neighbors = get_hex_neighbors(b)
        for n in neighbors:
            if n in bs_indexes:
                n_index = bs_indexes[n]
                for a in r_apps:
                    delay = app_link_delay[a][BS_DELAY_INDEX]
                    if isinstance(delay, list) or isinstance(delay, tuple):
                        delay = random.uniform(*delay)
                    graph[a][b_index][n_index] = delay
                    graph[a][n_index][b_index] = delay

    return graph


def gen_rand_users(nb_nodes, app_users):
    nb_bs = nb_nodes - 2
    users = [[0 for n in range(nb_nodes)] for a in app_users]
    for a, nb_users in enumerate(app_users):
        nodes = np.random.randint(nb_bs, size=int(nb_users))
        for n in nodes:
            users[a][n] += 1
    return users


def gen_nodes_capacity(nb_nodes):
    bs_capacity = {"CPU": 50.0, "STORAGE": 1000.0}
    core_capacity = {"CPU": 200.0, "STORAGE": 10000.0}
    nb_bs = nb_nodes - 2
    capacities = [bs_capacity for b in range(nb_bs)]
    capacities.append(core_capacity)
    resources = core_capacity.keys()
    cloud_capacity = {r: INF for r in resources}
    capacities.append(cloud_capacity)

    return capacities


def gen_rand_apps(nb_apps, nb_nodes, nb_users):
    apps = []
    nb_app_types = 3

    nb_embb = nb_apps // nb_app_types
    nb_urllc = nb_apps // nb_app_types
    nb_mmtc = nb_apps - nb_embb - nb_urllc
    nb_apps_per_type = [nb_embb, nb_urllc, nb_mmtc]

    users_embb = 0.2 * nb_users
    users_urllc = 0.1 * nb_users
    users_mmtc = nb_users - users_embb - users_urllc
    nb_users_per_type = [users_embb, users_urllc, users_mmtc]

    # [EMBB, URLlC, mMTC]
    deadline_per_type = [(10, 50), (1, 10), (50, 1000)]
    request_rate_per_type = [(0.02, 0.01), (0.02, 0.01), (0.001, 0.01)]
    work_size_per_type = [(1, 10), (1, 5), (1, 5)]
    storage_per_type = [(1, 50), (1, 10), (1, 10)]

    delay_per_type = [{"bs_bs": 1, "bs_core": 1, "core_cloud": 10},
                      {"bs_bs": 1, "bs_core": 1, "core_cloud": 10},
                      {"bs_bs": 1, "bs_core": 1, "core_cloud": 10}]

    # delay_per_type = [{"bs_bs": (1, 5), "bs_core": (1, 5), "core_cloud": (10, 50)},
    #                   {"bs_bs": (1, 5), "bs_core": (1, 5), "core_cloud": (10, 50)},
    #                   {"bs_bs": (1, 5), "bs_core": (1, 5), "core_cloud": (10, 50)}]

    for t in range(nb_app_types):
        for i in range(nb_apps_per_type[t]):
            deadline = deadline_per_type[t]
            if isinstance(deadline, list) or isinstance(deadline, tuple):
                deadline = round(random.uniform(*deadline), 2)

            work_size = work_size_per_type[t]
            if isinstance(work_size, list) or isinstance(work_size, tuple):
                work_size = random.randrange(*work_size)

            cpu_demand_1 = work_size + 1
            cpu_demand_2 = random.randrange(int(work_size + 1))

            storage_demand_1 = storage_per_type[t]
            storage_demand_2 = storage_per_type[t]
            if isinstance(storage_demand_1, list) or isinstance(storage_demand_1, tuple):
                storage_demand_1 = random.randrange(*storage_demand_1)
                storage_demand_2 = random.randrange(*storage_demand_2)

            request_rate = request_rate_per_type[t]
            if isinstance(request_rate, list) or isinstance(request_rate, tuple):
                request_rate = round(random.uniform(*request_rate), 4)

            max_instances = random.randrange(1, nb_nodes+1)
            # max_instances = nb_nodes

            users = nb_users_per_type[t] // nb_apps_per_type[t]
            if i == 0:
                users += nb_users_per_type[t] % nb_apps_per_type[t]

            app = {"deadline": deadline,
                   "max_instances": max_instances,
                   "request_rate": request_rate,
                   "work_size": work_size,
                   "users": users,
                   "demand": {"CPU": (cpu_demand_1, cpu_demand_2),
                              "STORAGE": (storage_demand_1, storage_demand_2)},
                   "delay": delay_per_type[t]}
            apps.append(app)

    return apps


def print_net_graph(graph):
    print "\n"
    size = len(graph)
    for i in range(size):
        for j in range(size):
            if(graph[i][j] == INF):
                print "%7s" % ("INF"),
            else:
                print "%7d\t" % (graph[i][j]),
            if j == size-1:
                print ""
