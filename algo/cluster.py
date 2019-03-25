import copy
import math
from functools import reduce
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import algo.util.constant as const
from algo.util.output import Output
from algo.util.sp import SP_Solver
from algo import minlp

# Constants
INF = const.INF
K1 = const.K1
K2 = const.K2
DEADLINE = const.DEADLINE
MAX_INSTANCES = const.MAX_INSTANCES
REQUEST_RATE = const.REQUEST_RATE
MAX_CLUSTERS = 10


class Cluster(SP_Solver):
    def __init__(self, input, time_limit=0):
        SP_Solver.__init__(self, input)
        self.time_limit = time_limit
        self.bs_map = input.bs_map
        self.users_map = input.users_map

    def solve(self):
        # Auxiliar Variables
        nb_nodes = len(self.nodes)
        r_nodes = range(nb_nodes)
        nb_apps = len(self.apps)
        r_apps = range(nb_apps)

        place = {(a, h): 0
                 for a in r_apps
                 for h in r_nodes}
        load = {(a, b, h): 0
                for a in r_apps
                for b in r_nodes
                for h in r_nodes}

        s_apps = sorted(r_apps, key=lambda a: self.apps[a][DEADLINE])
        current_capacity = copy.deepcopy(self.nodes)
        for app_index in s_apps:
            clusters = self._create_clusters(app_index)
            max_instances = self._get_clusters_max_instances(app_index, clusters)
            for c_index, cluster in enumerate(clusters):
                c_output = self._solve_cluster(app_index, cluster,
                                               current_capacity, max_instances[c_index])
                c_a = 0
                for c_h, h in enumerate(cluster):
                    if c_output.place[c_a, c_h]:
                        place[app_index, h] = 1
                    for c_b, b in enumerate(cluster):
                        load[app_index, b, h] += c_output.load[c_a, c_b, c_h]

                self._update_nodes_capacity(place, load, current_capacity)

        return self.local_search(place, load)

    def _create_clusters(self, app_index):
        nb_nodes = len(self.nodes)
        nb_bs = nb_nodes - 2

        features = []
        features_map = {}
        count = 0
        for bs_index in range(nb_bs):
            point = self.bs_map[bs_index].to_pixel()
            nb_users = self.users[app_index][bs_index]
            if nb_users > 0:
                # features.append([point.x, point.y, nb_users])
                features.append([point.x, point.y])
                features_map[count] = bs_index
                count += 1

        max_nb_clusters = min(MAX_CLUSTERS, len(features) - 1, self.apps[app_index][MAX_INSTANCES])
        nb_clusters = 1
        max_score = -1
        if max_nb_clusters > 1:
            for k in range(2, max_nb_clusters + 1):
                kmeans = KMeans(n_clusters=k)
                kmeans.fit(features)
                score = silhouette_score(features, kmeans.labels_)
                if score > max_score:
                    max_score = score
                    nb_clusters = k

        kmeans = KMeans(n_clusters=nb_clusters)
        kmeans.fit(features)
        labels = list(kmeans.labels_)

        clusters = [[] for _ in range(nb_clusters)]
        for index, cluster in enumerate(labels):
            node = features_map[index]
            clusters[cluster].append(node)

        return self._clusters_local_search(clusters, app_index)

    def _clusters_local_search(self, clusters, app_index):
        nb_nodes = len(self.nodes)
        r_nodes = range(nb_nodes)
        core_index = nb_nodes - 2
        cloud_index = nb_nodes - 1
        users = self.users[app_index]
        distances = self.net_delay[app_index]
        req_rate = self.apps[app_index][REQUEST_RATE]
        deadline = self.apps[app_index][DEADLINE]

        demands = [int(math.ceil(users[h] * req_rate)) for h in r_nodes]
        capacities = [0.0 for _ in r_nodes]
        for b in r_nodes:
            capacity = INF
            for r in self.resources:
                k1 = self.demand[app_index][r][K1]
                k2 = self.demand[app_index][r][K1]
                c = self.nodes[b][r]
                max_req = 0
                if k2 < c and k1 > 0:
                    max_req = (c - k2) / float(k1)
                elif k2 < c and k1 == 0:
                    max_req = INF
                else:
                    max_req = 0
                if max_req < capacity:
                    capacity = max_req
            capacities[b] = capacity

        f_nodes = list(filter(lambda i: demands[i] == 0
                              and capacities[i] > 0
                              and i != cloud_index
                              and i != core_index, r_nodes))

        for cluster in clusters:
            if len(cluster) == 0:
                continue

            c_demand = sum([demands[b] for b in cluster])
            c_capacity = sum([capacities[b] for b in cluster])

            if c_demand <= c_capacity:
                continue

            node = reduce(lambda m, i: m if users[m] > users[i] else i, cluster)
            s_nodes = sorted(f_nodes, key=lambda i: distances[node][i])
            for i in s_nodes:
                if distances[node][i] > deadline:
                    continue

                c_demand += demands[i]
                c_capacity += capacities[i]
                cluster.append(i)

                if c_demand <= c_capacity:
                    break

        for cluster in clusters:
            cluster.append(cloud_index)
            cluster.append(core_index)

        return clusters

    def _get_clusters_max_instances(self, app_index, clusters):
        nb_clusters = len(clusters)
        r_clusters = range(nb_clusters)
        max_instances = self.apps[app_index][MAX_INSTANCES]
        users = self.users[app_index]
        c_users = [sum([users[b] for b in c]) for c in clusters]
        total_users = float(sum(c_users))

        # print(c_users)
        # print(app_index, nb_clusters, total_users)
        # print(" ")

        def calc_max_instances(c):
            if total_users == 0 or nb_clusters > max_instances:
                return 1
            # return 1 + int(math.floor((max_instances - nb_clusters)
            #                           * c_users[c] / total_users))
            return int(math.floor(max_instances / nb_clusters))

        return [calc_max_instances(c) for c in r_clusters]

    def _get_cluster_input(self, app_index, cluster, capacities, max_instances=None):
        c_input = copy.deepcopy(self.input)
        if max_instances is not None:
            c_input.apps[app_index][MAX_INSTANCES] = max_instances
        c_input.apps = [c_input.apps[app_index]]
        c_input.apps_demand = [c_input.apps_demand[app_index]]
        c_input.nodes = [capacities[h] for h in cluster]
        c_input.users = [[c_input.users[a][h]
                          for h in cluster]
                         for a in [app_index]]
        c_input.net_delay = [[[c_input.net_delay[a][b][h]
                               for h in cluster]
                              for b in cluster]
                             for a in [app_index]]
        return c_input

    def _solve_cluster(self, app_index, cluster, capacities, max_instances):
        cluster_input = self._get_cluster_input(app_index, cluster, capacities, max_instances)
        return minlp.solve_sp(cluster_input, self.time_limit)

    def _update_nodes_capacity(self, place, distribution, result):
        nb_nodes = len(self.nodes)
        r_nodes = range(nb_nodes)
        nb_apps = len(self.apps)
        r_apps = range(nb_apps)

        for h in r_nodes:
            requests = [sum([distribution[a, b, h] for b in r_nodes])
                        for a in r_apps]
            for r in self.resources:
                demands = [place[a, h] * (self.demand[a][r][K1] * requests[a] + self.demand[a][r][K2])
                           for a in r_apps]
                result[h][r] = self.nodes[h][r] - sum(demands)
        return result


def solve_sp(input, time_limit=200):
    solver = Cluster(input, time_limit)
    result = solver.solve()
    return Output(input).set_solution(*result)
