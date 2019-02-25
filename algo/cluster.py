import copy
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import math
import sp
from minlp import MINLP

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


class Cluster(sp.Decoder):
    def __init__(self, input, time_limit=0):

        sp.Decoder.__init__(self, input)
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
        distribution = {(a, b, h): 0
                        for a in r_apps
                        for b in r_nodes
                        for h in r_nodes}

        r_apps.sort(key=lambda a: self.apps[a][DEADLINE])
        current_capacity = copy.deepcopy(self.nodes)
        for app_index in r_apps:
            clusters = self._create_clusters(app_index)
            max_instances = self._get_clusters_max_instances(app_index, clusters)
            for index_c, cluster in enumerate(clusters):
                result = self._solve_cluster(app_index, cluster,
                                             current_capacity, max_instances[index_c])
                for h in cluster:
                    if result[0][h]:
                        place[app_index, h] = 1
                    for b in cluster:
                        distribution[app_index, b, h] += result[1][b, h]
                self._update_nodes_capacity(place, distribution, current_capacity)

        return self._decode_local_search(place, distribution)

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

    def _get_cluster_output(self, result, app_index, cluster):
        place_c, distribution_c = result

        place = {}
        distribution = {}

        a_c = 0
        for h_c, h in enumerate(cluster):
            place[h] = place_c[a_c, h_c]
            for b_c, b in enumerate(cluster):
                distribution[b, h] = distribution_c[a_c, b_c, h_c]

        return place, distribution

    def _solve_cluster(self, app_index, cluster, capacities, max_instances):
        cluster_input = self._get_cluster_input(app_index, cluster, capacities, max_instances)

        solver = MINLP(cluster_input, self.time_limit)
        result = list(solver.solve())
        result.pop(0)
        return self._get_cluster_output(result, app_index, cluster)

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
    result = list(solver.solve())

    e = solver.calc_qos_violation(*result)
    place = solver.get_places(*result)
    distribution = solver.get_distributions(*result)

    return e, place, distribution
