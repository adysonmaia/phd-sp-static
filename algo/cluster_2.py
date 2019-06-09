from algo.util.output import Output
from algo.cluster import Cluster
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score


class Cluster_Kmeans(Cluster):
    def __init__(self, input, solver=None, solver_params=None):
        Cluster.__init__(self, input, solver, solver_params)

    def _create_clusters(self, app_index):
        nb_nodes = len(self.nodes)
        r_nodes = range(nb_nodes)
        app = self.apps[app_index]

        features = []
        features_map = {}
        count = 0
        for node_index in r_nodes:
            node = self.nodes[node_index]
            if node.is_base_station() and self.get_nb_users(app_index, node_index) > 0:
                point = node.point.to_pixel()
                features.append([point.x, point.y])
                features_map[count] = node_index
                count += 1

        max_nb_clusters = min(len(features) - 1, app.max_instances)
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

        return self._gen_clusters_data(app_index, clusters)


def solve(input,
          solver=None,
          solver_params=None):

    c_solver = Cluster_Kmeans(input, solver, solver_params)
    result = c_solver.solve()
    return Output(input).set_solution(*result)
