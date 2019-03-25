import copy
import algo.util.constant as const
from algo.util.output import Output
from algo.util.kmedoids import KMedoids
from algo.cluster import Cluster

# Constants
DEADLINE = const.DEADLINE
MAX_INSTANCES = const.MAX_INSTANCES
MAX_CLUSTERS = 10


class Cluster_2(Cluster):
    def __init__(self, input, time_limit=0):
        Cluster.__init__(self, input, time_limit)

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
        r_nodes = range(nb_nodes)

        distances = self.net_delay[app_index]
        features = list(filter(lambda h: self.users[app_index][h] > 0, r_nodes))
        max_nb_clusters = min(MAX_CLUSTERS, len(features), self.apps[app_index][MAX_INSTANCES])

        kmedoids = KMedoids()
        nb_clusters = 1
        max_score = -1
        if max_nb_clusters > 1:
            for k in range(1, max_nb_clusters + 1):
                clusters = kmedoids.fit(k, features, distances)
                score = kmedoids.silhouette_score(clusters, distances)
                if score > max_score:
                    max_score = score
                    nb_clusters = k

        clusters = kmedoids.fit(nb_clusters, features, distances)
        return self._clusters_local_search(clusters, app_index)


def solve_sp(input, time_limit=200):
    solver = Cluster_2(input, time_limit)
    result = solver.solve()
    return Output(input).set_solution(*result)
