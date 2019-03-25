import math
import algo.util.constant as const
from algo.util.output import Output
from algo.util.brkga import BRKGA
from algo.genetic import SP_Chromosome

INF = const.INF
K1 = const.K1
K2 = const.K2
CPU = const.CPU
REQUEST_RATE = const.REQUEST_RATE
MAX_INSTANCES = const.MAX_INSTANCES
WORK_SIZE = const.WORK_SIZE
POOL_SIZE = 0


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

        self.nb_genes = nb_apps * (nb_nodes + 1) + len(self.requests)

    def gen_init_population(self):
        indiv = [0 for _ in range(self.nb_genes)]
        return [indiv]

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
            start = nb_apps + a * nb_nodes
            end = start + nb_nodes + 1
            priority = individual[start+1:end]
            nodes = list(r_nodes)
            nodes.sort(key=lambda v: priority[v], reverse=True)
            percentage = individual[a]
            nb_instances = int(math.ceil(percentage * self.apps[a][MAX_INSTANCES]))
            max_nodes = min(nb_nodes, nb_instances)
            selected_nodes.append(nodes[:max_nodes])

            # print(self.apps[a][MAX_INSTANCES], nb_instances)

        capacity = {(h, r): 0 for h in r_nodes for r in self.resources}

        start = nb_apps * (nb_nodes + 1)
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
             nb_generations=300,
             population_size=300,
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
