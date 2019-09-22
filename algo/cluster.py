import math
from algo.util.output import Output
from algo.util.sp import SP_Solver
from algo.util.kmedoids import KMedoids
import algo


class Cluster(SP_Solver):
    def __init__(self, input, solver=None, solver_params=None):
        SP_Solver.__init__(self, input)

        if not solver:
            # solver = algo.genetic_mo
            # solver = algo.milp
            # solver = algo.greedy
            solver = algo.genetic
        self.solver = solver
        if not solver_params:
            solver_params = {}
        self.solver_params = solver_params

    def solve(self):
        r_nodes = range(len(self.nodes))
        r_apps = range(len(self.apps))

        place = {(a, h): 0
                 for a in r_apps
                 for h in r_nodes}
        load = {(a, b, h): 0
                for a in r_apps
                for b in r_nodes
                for h in r_nodes}

        s_apps = sorted(r_apps, key=lambda a: self.apps[a].deadline)
        for app_index in s_apps:
            clusters = self._create_clusters(app_index)
            for cluster in clusters:
                self._update_input(cluster, place, load)
                self.solver_params['input'] = cluster.input
                cluster.output = self.solver.solve(**self.solver_params)
                self._update_output(cluster, place, load)

        return self.local_search(place, load)

    def _create_clusters(self, app_index):
        nb_nodes = len(self.nodes)
        r_nodes = range(nb_nodes)
        app = self.apps[app_index]

        distances = [[app.get_net_delay(i, j)
                      for j in self.nodes]
                     for i in self.nodes]
        features = list(filter(lambda h: app.get_nb_users(self.nodes[h]) > 0, r_nodes))

        kmedoids = KMedoids()
        nb_clusters = self._select_nb_clusters(app_index, features, distances)
        clusters = kmedoids.fit(nb_clusters, features, distances)
        return self._gen_clusters_data(app_index, clusters)

    def _select_nb_clusters(self, app_index, features, distances):
        app = self.apps[app_index]
        max_nb_clusters = min(len(features), app.max_instances)

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

        return nb_clusters

    def _gen_clusters_data(self, app_index, clusters):
        nb_clusters = len(clusters)
        app = self.apps[app_index]

        max_instances = int(math.floor(app.max_instances / nb_clusters))
        data = []
        for c in range(nb_clusters):
            cluster = Cluster_Data()
            cluster.app = app
            cluster.app_index = app_index

            node_indexes = clusters[c]
            node_indexes.append(self.get_core_index())
            node_indexes.append(self.get_cloud_index())
            cluster.node_indexes = node_indexes

            c_input = self.input.filter([app_index], node_indexes)
            c_input.apps[0].max_instances = max_instances
            cluster.input = c_input

            data.append(cluster)

        return data

    def _update_input(self, cluster, place, load):
        r_nodes = range(len(self.nodes))
        r_apps = range(len(self.apps))

        for c_h, h in enumerate(cluster.node_indexes):
            c_node = cluster.input.nodes[c_h]
            for r in self.resources:
                demand = 0
                for a in r_apps:
                    app = self.apps[a]
                    k1, k2 = app.get_demand(r)
                    node_load = int(sum([load[a, b, h] for b in r_nodes]))
                    demand += float(place[a, h] * (node_load * k1 + k2))
                capacity = c_node.get_capacity(r) - demand
                c_node.set_capacity(r, capacity)

        return cluster

    def _update_output(self, cluster, place, load):
        a = cluster.app_index
        c_a = 0
        c_place, c_load = cluster.output.get_vars()

        for c_h, h in enumerate(cluster.node_indexes):
            if c_place[c_a, c_h]:
                place[a, h] = 1
            for c_b, b in enumerate(cluster.node_indexes):
                load[a, b, h] += c_load[c_a, c_b, c_h]

        return place, load


class Cluster_Data:
    def __init__(self):
        self.app = None
        self.app_index = 0
        self.node_indexes = None
        self.input = None
        self.output = None


def solve(input,
          solver=None,
          solver_params=None):

    c_solver = Cluster(input, solver, solver_params)
    result = c_solver.solve()
    return Output(input).set_solution(*result)
