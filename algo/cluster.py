import copy
import math
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from algo.util.output import Output
from algo.util.sp import SP_Solver
from algo import minlp

# Constants
INF = float("inf")
MAX_CLUSTERS = 10
QUEUE_MIN_DIFF = 0.00001
E_MAX = 1000.0
K1 = 0
K2 = 1
CPU = "CPU"
DEADLINE = "deadline"
MAX_INSTANCES = "max_instances"
REQUEST_RATE = "request_rate"
WORK_SIZE = "work_size"


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
        # r_nodes = range(nb_nodes)
        cloud_index = nb_nodes - 1
        core_index = nb_nodes - 2

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

        # nb_clusters = min(4, len(features), self.apps[app_index][MAX_INSTANCES])

        kmeans = KMeans(n_clusters=nb_clusters)
        kmeans.fit(features)
        labels = list(kmeans.labels_)

        clusters = [[] for _ in range(nb_clusters)]
        for index, cluster in enumerate(labels):
            node = features_map[index]
            clusters[cluster].append(node)

        # users = self.users[app_index]
        # for bs_index, bs in enumerate(self.bs_map):
        #     if users[bs_index] > 0:
        #         continue
        #     insert_list = []
        #     for cluster_index, cluster in enumerate(clusters):
        #         for node_index in cluster:
        #             node = self.bs_map[node_index]
        #             if node.get_distance(bs) <= 1:
        #                 insert_list.append(cluster_index)
        #                 break
        #     for cluster_index in insert_list:
        #         clusters[cluster_index].append(bs_index)

        for cluster in clusters:
            cluster.append(cloud_index)
            cluster.append(core_index)

        return clusters

    def _get_clusters_max_instances(self, app_index, clusters):
        nb_clusters = len(clusters)
        max_instances = self.apps[app_index][MAX_INSTANCES]
        max_instances = int(math.floor(max_instances / nb_clusters))
        return [max_instances] * nb_clusters

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
