import math
import random
from algo.genetic import SP_Chromosome
from algo.brkga import BRKGA

INF = float("inf")
POOL_SIZE = 0
K1 = 0
K2 = 1
CPU = "CPU"
DEADLINE = "deadline"
MAX_INSTANCES = "max_instances"
REQUEST_RATE = "request_rate"
WORK_SIZE = "work_size"


class SP3_Chromosome(SP_Chromosome):
    def __init__(self, input):
        SP_Chromosome.__init__(self, input)

        nb_apps = len(self.apps)
        r_apps = range(nb_apps)
        nb_nodes = len(self.nodes)
        r_nodes = range(nb_nodes)

        self.requests = []
        for a in r_apps:
            for b in r_nodes:
                nb_requests = int(math.ceil(self.users[a][b] * self.apps[a][REQUEST_RATE]))
                self.requests += [(a, b)] * nb_requests

        self.nb_genes = nb_apps * nb_nodes + len(self.requests) + nb_nodes * nb_nodes

    def gen_init_population(self):
        return []

    def decode(self, individual):
        nb_apps = len(self.apps)
        r_apps = range(nb_apps)
        nb_nodes = len(self.nodes)
        r_nodes = range(nb_nodes)
        nb_requests = len(self.requests)
        r_requests = range(nb_requests)
        cloud = nb_nodes - 1

        place = {(a, h): 0
                 for h in r_nodes
                 for a in r_apps}
        load = {(a, b, h): 0
                for h in r_nodes
                for b in r_nodes
                for a in r_apps}

        selected_nodes = []
        for a in r_apps:
            start = a * nb_nodes
            end = start + nb_nodes + 1
            priority = individual[start:end]
            nodes = r_nodes[:]
            nodes.sort(key=lambda v: priority[v], reverse=True)
            max_nodes = min(nb_nodes, self.apps[a][MAX_INSTANCES])
            selected_nodes.append(nodes[:max_nodes])

        capacity = {(h, r): 0 for h in r_nodes for r in self.resources}

        start = nb_apps * nb_nodes
        end = start + nb_requests + 1
        priority = individual[start:end]

        r_requests.sort(key=lambda v: priority[v], reverse=True)
        for req in r_requests:
            a, b = self.requests[req]

            start = nb_apps * nb_nodes + nb_requests + b * nb_nodes
            # end = start + nb_nodes + 1
            end = start + len(selected_nodes[a]) + 1
            cdf = individual[start:end]

            sum_total = float(sum(cdf))
            cdf_size = len(cdf)
            if sum_total == 0.0:
                cdf = [1.0 / cdf_size] * cdf_size
                sum_total = 1.0
            cdf.sort()
            sum_current = 0
            for i in range(cdf_size):
                sum_current += cdf[i]
                cdf[i] = sum_current / sum_total

            nodes = list(selected_nodes[a])
            nodes.append(cloud)
            fit = False
            while not fit:
                h = 0
                value = random.random()
                for index, probability in enumerate(cdf):
                    if value <= probability:
                        h = nodes[index]
                        break

                fit = True
                resources = {}
                for r in self.resources:
                    value = (capacity[h, r]
                             + self.demand[a][r][K1]
                             + (1 - place[a, h]) * self.demand[a][r][K2])
                    resources[r] = value
                    fit = fit and (value <= self.nodes[h][r])

                if fit:
                    load[a, b, h] += 1
                    place[a, h] = 1
                    for r in self.resources:
                        capacity[h, r] = resources[r]

        return self._decode_local_search(place, load)

    # def _decode_node_priority(self, indiv, a, b, h, place, load):
    #     nb_nodes = len(self.nodes)
    #     r_nodes = range(nb_nodes)
    #
    #     cloud_delay = self.net_delay[a][b][nb_nodes - 1]
    #     node_delay = self.net_delay[a][b][h]
    #     delay = (cloud_delay - node_delay) / cloud_delay
    #
    #     max_load = sum([load[a, b, v] for v in r_nodes])
    #     max_load = float(max_load) if max_load > 0 else 1.0
    #
    #     return delay + load[a, b, h] / max_load


def solve_sp(input,
             nb_generations=200,
             population_size=100,
             elite_proportion=0.4,
             mutant_proportion=0.3):

    chromossome = SP3_Chromosome(input)
    genetic = BRKGA(chromossome,
                    nb_generations=nb_generations,
                    population_size=population_size,
                    elite_proportion=elite_proportion,
                    mutant_proportion=mutant_proportion,
                    pool_size=POOL_SIZE)

    population = genetic.solve()

    data_decoded = chromossome.decode(population[0])
    e = chromossome.calc_qos_violation(*data_decoded)
    place = chromossome.get_places(*data_decoded)
    distribution = chromossome.get_distributions(*data_decoded)

    return e, place, distribution
