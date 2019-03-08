import math
from algo.util.output import Output
from algo.util.sp import SP_Solver
from algo.util.brkga import Chromosome, BRKGA

INF = float("inf")
POOL_SIZE = 0
K1 = 0
K2 = 1
CPU = "CPU"
DEADLINE = "deadline"
MAX_INSTANCES = "max_instances"
REQUEST_RATE = "request_rate"
WORK_SIZE = "work_size"


class SP_Chromosome(Chromosome, SP_Solver):
    def __init__(self, input):
        Chromosome.__init__(self)
        SP_Solver.__init__(self, input)
        self.nb_genes = len(self.apps) * (2 * len(self.nodes) + 1)

    def gen_init_population(self):
        nb_apps = len(self.apps)
        r_apps = range(nb_apps)
        nb_nodes = len(self.nodes)
        r_nodes = range(nb_nodes)

        indiv = [0.0 for g in range(self.nb_genes)]

        count = 0
        total = float(nb_apps * nb_nodes)
        s_apps = sorted(r_apps, key=lambda a: self.apps[a][DEADLINE])
        for a in s_apps:
            s_nodes = sorted(r_nodes, key=lambda b: self.users[a][b],
                             reverse=True)
            for b in s_nodes:
                indiv[a*nb_nodes + b] = (total - count) / total
                count += 1

        return [indiv]

    def stopping_criteria(self, population):
        best_indiv = population[0]
        best_value = best_indiv[self.nb_genes]
        # print("best: {}".format(best_value))
        return best_value == 0.0

    def fitness(self, individual):
        result = self.decode(individual)
        return self.metric.get_qos_violation(*result)

    def decode(self, individual):
        nb_apps = len(self.apps)
        r_apps = range(nb_apps)
        nb_nodes = len(self.nodes)
        r_nodes = range(nb_nodes)

        place = {(a, h): 0
                 for h in r_nodes
                 for a in r_apps}
        load = {(a, b, h): 0
                for h in r_nodes
                for b in r_nodes
                for a in r_apps}

        capacity = {(h, r): 0 for h in r_nodes for r in self.resources}

        apps_priority = {(a, b): individual[a * nb_nodes + b]
                         for a in r_apps
                         for b in r_nodes}
        apps_priority = sorted(apps_priority.items(), key=lambda i: i[1],
                               reverse=True)

        for (a, b), v in apps_priority:
            if self.users[a][b] == 0:
                continue
            app = self.apps[a]
            total_requests = int(math.ceil(self.users[a][b] * app[REQUEST_RATE]))

            nodes_priority = list(r_nodes)
            nodes_priority.sort(key=lambda h:
                                self._node_priority(individual, a, b, h),
                                reverse=True)

            for h in nodes_priority:
                requests = total_requests
                while requests > 0 and total_requests > 0:
                    fit = True
                    resources = {}
                    for r in self.resources:
                        value = (capacity[h, r]
                                 + requests * self.demand[a][r][K1]
                                 + (1 - place[a, h]) * self.demand[a][r][K2])
                        resources[r] = value
                        fit = fit and (value <= self.nodes[h][r])

                    if fit:
                        load[a, b, h] += requests
                        place[a, h] = 1
                        total_requests -= requests
                        requests = 0
                        for r in self.resources:
                            capacity[h, r] = resources[r]
                    else:
                        requests -= 1
                if total_requests == 0:
                    break

        return self.local_search(place, load)

    def _node_priority(self, individual, app, bs, node):
        nb_apps = len(self.apps)
        nb_nodes = len(self.nodes)

        cloud_delay = self.net_delay[app][bs][nb_nodes - 1]
        node_delay = self.net_delay[app][bs][node]
        delay = (cloud_delay - node_delay) / cloud_delay

        weight = round(individual[nb_apps * nb_nodes + app], 2)
        value = individual[nb_apps * (nb_nodes + 1) + app * nb_nodes + node]

        return weight * value + (1.0 - weight) * delay


def solve_sp(input,
             nb_generations=200,
             population_size=100,
             elite_proportion=0.4,
             mutant_proportion=0.3):

    chromossome = SP_Chromosome(input)
    genetic = BRKGA(chromossome,
                    nb_generations=nb_generations,
                    population_size=population_size,
                    elite_proportion=elite_proportion,
                    mutant_proportion=mutant_proportion,
                    pool_size=POOL_SIZE)

    population = genetic.solve()
    result = chromossome.decode(population[0])
    return Output(input).set_solution(*result)
