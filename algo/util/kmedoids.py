import random
INF = float("inf")


class KMedoids():
    def __init__(self, max_iterations=300):
        self.max_iterations = max_iterations
        self.last_metoids = []

    def fit(self, nb_clusters, data, distances):
        r_clusters = range(nb_clusters)

        labels = {v: -1 for v in data}
        metoids = self._initial_metoids(nb_clusters, data, distances)

        clusters = None
        changed = True
        iter = 0
        while iter < self.max_iterations and changed:
            clusters = [[] for _ in r_clusters]
            changed = False
            for v in data:
                min_dist = INF
                new_label = -1
                for label in r_clusters:
                    metoid = metoids[label]
                    if distances[v][metoid] <= min_dist:
                        new_label = label
                        min_dist = distances[v][metoid]
                if new_label != labels[v]:
                    changed = True
                labels[v] = new_label
                clusters[new_label].append(v)

            for label in r_clusters:
                cluster = clusters[label]
                metoid = metoids[label]
                min_sum_dist = INF
                for v in cluster:
                    sum_dist = sum([distances[v][u] for u in cluster])
                    if sum_dist < min_sum_dist:
                        min_sum_dist = sum_dist
                        metoid = v
                metoids[label] = metoid

            iter = iter + 1
        self.last_metoids = metoids

        return clusters

    def get_last_metoids(self):
        return self.last_metoids

    # def _initial_metoids(self, nb_clusters, data, distances):
    #     metoids = random.sample(data, k=nb_clusters)
    #     return metoids

    def _initial_metoids(self, nb_clusters, data, distances):
        r_data = range(len(data))
        priority = {v: 0.0 for v in data}
        sum_dist = [sum([distances[i][l] for l in data]) for i in data]

        for j in r_data:
            for i in r_data:
                if sum_dist[i] > 0.0:
                    datum_i = data[i]
                    datum_j = data[j]
                    priority[datum_j] += distances[datum_i][datum_j] / sum_dist[i]

        s_data = sorted(data, key=lambda i: priority[i])
        metoids = s_data[:nb_clusters]
        return metoids

    def silhouette_score(self, clusters, distances):
        nb_clusters = len(clusters)
        r_clusters = range(nb_clusters)
        if nb_clusters <= 1:
            return 0.0
        s = sum([self._cluster_silhouette(label, clusters, distances) for label in r_clusters])
        s = s / float(len(clusters))
        return s

    def _cluster_silhouette(self, label, clusters, distances):
        c = clusters[label]
        cluster_size = len(c)
        if cluster_size <= 1:
            return 0.0
        s = sum([self._datum_silhouette(datum, label, clusters, distances) for datum in c])
        s = s / float(cluster_size)
        return s

    def _datum_silhouette(self, datum, label, clusters, distances):
        cluster = clusters[label]
        if len(cluster) <= 1 or len(clusters) <= 1:
            return 0.0

        a = sum([distances[datum][v] for v in cluster]) / float(len(cluster))
        b = INF
        for c_label, c in enumerate(clusters):
            if c_label == label or len(c) == 0:
                continue
            c_b = sum([distances[datum][v] for v in c]) / float(len(c))
            if c_b < b:
                b = c_b

        if b == 0.0 and a == 0.0:
            return 0.0
        return (b - a) / float(max(b, a))
