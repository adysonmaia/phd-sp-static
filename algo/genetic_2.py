import math
from algo.util.output import Output
from algo.util.brkga import BRKGA
from algo.genetic import SP_Chromosome

INF = float("inf")
POOL_SIZE = 0
K1 = 0
K2 = 1
CPU = "CPU"
DEADLINE = "deadline"
MAX_INSTANCES = "max_instances"
REQUEST_RATE = "request_rate"
WORK_SIZE = "work_size"


class SP2_Chromosome(SP_Chromosome):
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

        self.nb_genes = nb_apps * nb_nodes + len(self.requests)

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
        app_load = {(a, h): 0
                    for h in r_nodes
                    for a in r_apps}

        selected_nodes = []
        for a in r_apps:
            start = a * nb_nodes
            # end = start + nb_nodes + 1
            end = start + nb_nodes
            priority = individual[start:end]
            nodes = list(r_nodes)
            nodes.sort(key=lambda v: priority[v], reverse=True)
            max_nodes = min(nb_nodes, self.apps[a][MAX_INSTANCES])
            selected_nodes.append(nodes[:max_nodes])

        capacity = {(h, r): 0 for h in r_nodes for r in self.resources}

        start = nb_apps * nb_nodes
        end = start + nb_requests
        priority = individual[start:end]

        s_requests = sorted(r_requests, key=lambda v: priority[v], reverse=True)
        for req in s_requests:
            a, b = self.requests[req]
            nodes = list(selected_nodes[a])
            nodes.sort(key=lambda h: self._node_priority(individual, a, b, h, app_load))
            nodes.append(cloud)
            for h in nodes:
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
                    app_load[a, h] += 1
                    place[a, h] = 1
                    for r in self.resources:
                        capacity[h, r] = resources[r]
                    break

        return self.local_search(place, load)

    def _node_priority(self, indiv, a, b, h, app_load):
        work_size = self.apps[a][WORK_SIZE]
        cpu_k1 = self.demand[a][CPU][K1]
        cpu_k2 = self.demand[a][CPU][K2]

        proc_delay = 0.0
        net_delay = self.net_delay[a][b][h]

        node_load = 1 + app_load[a, h]
        proc_delay_divisor = float(node_load * (cpu_k1 - work_size) + cpu_k2)
        if proc_delay_divisor > 0.0:
            proc_delay = work_size / proc_delay_divisor
        else:
            proc_delay = INF

        return net_delay + proc_delay


def solve_sp(input,
             nb_generations=200,
             population_size=100,
             elite_proportion=0.4,
             mutant_proportion=0.3):

    chromossome = SP2_Chromosome(input)
    genetic = BRKGA(chromossome,
                    nb_generations=nb_generations,
                    population_size=population_size,
                    elite_proportion=elite_proportion,
                    mutant_proportion=mutant_proportion,
                    pool_size=POOL_SIZE)

    population = genetic.solve()
    result = chromossome.decode(population[0])
    return Output(input).set_solution(*result)
