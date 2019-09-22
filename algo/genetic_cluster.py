import math
from algo.util.output import Output
from algo.util.sp import SP_Solver
from algo.util.brkga import Chromosome, BRKGA
from algo.util.kmedoids import KMedoids

INF = float("inf")
POOL_SIZE = 0
REQ_BLOCK_SIZE = 1000


class App_Clusters:
    def __init__(self, app_index, clusters, max_instances):
        self.app_index = app_index
        self.clusters = clusters
        self.max_instances = max_instances
        self.nb_clusters = len(clusters)
        self.node_cluster = {}

        for cluster_index in range(self.nb_clusters):
            cluster = self.clusters[cluster_index]
            for node_index in cluster:
                self.node_cluster[node_index] = cluster_index

    def get_node_cluster_index(self, node_index):
        return self.node_cluster[node_index]

    def get_node_cluster(self, node_index):
        cluster_index = self.node_cluster[node_index]
        return self.clusters[cluster_index]

    def get_cluster_nodes(self, cluster_index):
        return self.clusters[cluster_index]

    def get_cluster_max_instances(self, cluster_index):
        return self.max_instances[cluster_index]


class Request_Block:
    def __init__(self, app_index, source_node_index, nb_requests):
        self.app_index = app_index
        self.source_node_index = source_node_index
        self.nb_requests = nb_requests


class Cluster_Chromosome(Chromosome, SP_Solver):
    def __init__(self, input, objective=None):
        Chromosome.__init__(self)
        SP_Solver.__init__(self, input)

        nb_apps = len(self.apps)
        r_apps = range(nb_apps)
        nb_nodes = len(self.nodes)
        r_nodes = range(nb_nodes)

        if objective is None:
            objective = self.metric.get_qos_violation
        self.objective = objective

        self.app_clusters = {}
        self.app_max_nb_clusters = [0 for _ in r_apps]
        self.app_nb_clusters = [0 for _ in r_apps]

        self.requests = []
        for a in r_apps:
            for b in r_nodes:
                total_requests = self.get_nb_requests(a, b)
                block_size = REQ_BLOCK_SIZE
                nb_blocks = int(math.ceil(total_requests / float(block_size)))
                for _ in range(nb_blocks):
                    requests = block_size
                    if total_requests < block_size:
                        requests = total_requests
                    total_requests -= requests
                    self.requests.append(Request_Block(a, b, requests))

        self.nb_genes = nb_apps * (nb_nodes + 1) + len(self.requests)
        print("{} = {} + {} + {}".format(
            self.nb_genes, nb_apps, nb_apps * nb_nodes, len(self.requests))
        )

    def gen_init_population(self):
        self._create_clusters()

        indiv_0 = [0] * self.nb_genes
        indiv_1 = self._gen_greedy_individual()

        return [indiv_0, indiv_1]

    def stopping_criteria(self, population):
        best_indiv = population[0]
        best_value = best_indiv[self.nb_genes]
        return best_value == 0.0

    def fitness(self, individual):
        # start_time = time.time()
        result = self.decode(individual)
        value = self.objective(*result)
        # elapsed_time = round(time.time() - start_time, 4)
        # print(elapsed_time)
        return value

    def _create_clusters(self):
        r_nodes = range(len(self.nodes))
        r_apps = range(len(self.apps))

        for a in r_apps:
            app_max_instances = self.apps[a].max_instances
            distances = [[self.get_net_delay(a, i, j)
                          for j in r_nodes]
                         for i in r_nodes]

            kmedoids = KMedoids()
            features = list(filter(lambda h: self.get_nb_users(a, h) > 0, r_nodes))
            max_nb_clusters = min(len(features), app_max_instances)
            self.app_max_nb_clusters[a] = max_nb_clusters
            self.app_nb_clusters[a] = max_nb_clusters

            max_score = -1
            for k in range(1, max_nb_clusters + 1):
                clusters = kmedoids.fit(k, features, distances)
                score = kmedoids.silhouette_score(clusters, distances)
                if score > max_score:
                    max_score = score
                    self.app_nb_clusters[a] = k

                instances = []
                for c in clusters:
                    # TODO improve the max instances calculation
                    instances.append(int(math.floor(app_max_instances / k)))
                self.app_clusters[a, k] = App_Clusters(a, clusters, instances)

    def decode(self, individual):
        nb_apps = len(self.apps)
        r_apps = range(nb_apps)
        nb_nodes = len(self.nodes)
        r_nodes = range(nb_nodes)
        nb_requests = len(self.requests)
        r_requests = range(nb_requests)
        cloud = self.get_cloud_index()
        core = self.get_core_index()

        place = {(a, h): 0
                 for h in r_nodes
                 for a in r_apps}
        load = {(a, b, h): 0
                for h in r_nodes
                for b in r_nodes
                for a in r_apps}
        app_load = {(a, h): 0
                    for h in r_nodes
                    for a in r_apps}

        selected_clusters = {}
        selected_nodes = {}
        for a in r_apps:
            percentage = individual[a]
            # percentage = max(1.0, percentage)
            max_nb_clusters = self.app_max_nb_clusters[a]
            nb_clusters = max(1, int(math.ceil(percentage * max_nb_clusters)))
            # nb_clusters = self.app_nb_clusters[a]

            clusters = self.app_clusters[a, nb_clusters]
            selected_clusters[a] = clusters

            start = nb_apps + a * nb_nodes
            end = start + nb_nodes
            priority = individual[start:end]

            for k in range(nb_clusters):
                nodes = list(clusters.get_cluster_nodes(k))
                nodes.sort(key=lambda v: priority[v], reverse=True)
                max_nodes = clusters.get_cluster_max_instances(k)
                selected_nodes[a, k] = nodes[:max_nodes]

        resource_used = {(h, r): 0 for h in r_nodes for r in self.resources}

        start = nb_apps * (nb_nodes + 1)
        end = start + nb_requests
        priority = individual[start:end]

        s_requests = sorted(r_requests, key=lambda v: priority[v], reverse=True)
        for req_index in s_requests:
            req_block = self.requests[req_index]
            nb_requests = req_block.nb_requests
            a = req_block.app_index
            b = req_block.source_node_index

            clusters = selected_clusters[a]
            k = clusters.get_node_cluster_index(b)
            nodes = list(selected_nodes[a, k])
            # TODO improve _node_priority function
            nodes.sort(key=lambda h: self._node_priority(individual, req_block, h, app_load))
            nodes.append(core)
            nodes.append(cloud)
            for h in nodes:
                fit = True
                resources = {}
                for r in self.resources:
                    k1, k2 = self.apps[a].get_demand(r)
                    value = resource_used[h, r]
                    value += k1 * nb_requests + k2 * (1 - place[a, h])
                    capacity = self.nodes[h].get_capacity(r)
                    resources[r] = value
                    fit = fit and (value <= capacity)

                if fit:
                    load[a, b, h] += nb_requests
                    app_load[a, h] += nb_requests
                    place[a, h] = 1
                    for r in self.resources:
                        resource_used[h, r] = resources[r]
                    break

        return self.local_search(place, load)

    def _node_priority(self, indiv, req_block, h, app_load):
        a = req_block.app_index
        b = req_block.source_node_index
        nb_requests = req_block.nb_requests
        app = self.apps[a]
        work_size = app.work_size
        cpu_k1, cpu_k2 = app.get_cpu_demand()

        proc_delay = 0.0
        net_delay = self.get_net_delay(a, b, h)

        # new request + current load
        node_load = nb_requests + app_load[a, h]
        proc_delay_divisor = float(node_load * (cpu_k1 - work_size) + cpu_k2)
        if proc_delay_divisor > 0.0:
            proc_delay = work_size / proc_delay_divisor
        else:
            proc_delay = INF

        return net_delay + proc_delay

    def _gen_greedy_individual(self):
        """Create an individual that is decoded
        to a similar solution of the greedy algorithm
        See Also: greedy.py
        """
        nb_apps = len(self.apps)
        r_apps = range(nb_apps)
        nb_nodes = len(self.nodes)
        r_nodes = range(nb_nodes)

        indiv = [0] * self.nb_genes

        max_deadline = 0.0
        for a in r_apps:
            indiv[a] = 1.0

            deadline = self.apps[a].deadline
            if deadline > max_deadline:
                max_deadline = deadline

            nodes_delay = []
            max_delay = 0.0

            for h in r_nodes:
                avg_delay = 0.0
                count = 0
                for b in r_nodes:
                    if self.get_nb_users(a, b) > 0:
                        avg_delay += self.get_net_delay(a, b, h)
                        count += 1
                if count > 0:
                    avg_delay = avg_delay / float(count)
                nodes_delay.append(avg_delay)
                if avg_delay > max_delay:
                    max_delay = avg_delay

            if max_delay == 0.0:
                max_delay = 1.0

            for h in r_nodes:
                key = nb_apps + a * nb_nodes + h
                value = 1.0 - nodes_delay[h] / float(max_delay)
                indiv[key] = value

        if max_deadline == 0.0:
            max_deadline = 1.0

        for req_index in range(len(self.requests)):
            req_block = self.requests[req_index]
            a = req_block.app_index
            b = req_block.source_node_index
            key = nb_apps * (nb_nodes + 1) + req_index
            value = 1.0 - self.apps[a].deadline / float(max_deadline)
            indiv[key] = value

        return indiv


def solve(input,
          nb_generations=100,
          population_size=100,
          elite_proportion=0.1,
          mutant_proportion=0.2,
          elite_probability=0.6,
          objective=None):

    chromossome = Cluster_Chromosome(input, objective)
    genetic = BRKGA(chromossome,
                    nb_generations=nb_generations,
                    population_size=population_size,
                    elite_proportion=elite_proportion,
                    mutant_proportion=mutant_proportion,
                    elite_probability=elite_probability,
                    pool_size=POOL_SIZE)

    population = genetic.solve()
    result = chromossome.decode(population[0])
    return Output(input).set_solution(*result)
