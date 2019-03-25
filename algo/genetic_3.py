import math
import random
import algo.util.constant as const
from algo.util.output import Output
from algo.util.brkga import BRKGA
from algo.genetic import SP_Chromosome

INF = const.INF
K1 = const.K1
K2 = const.K2
REQUEST_RATE = const.REQUEST_RATE
MAX_INSTANCES = const.MAX_INSTANCES
POOL_SIZE = 0
VIOL_PENALITY = 1000


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

        self.nb_genes = len(self.requests)

    # def gen_rand_individual(self):
    #     nb_nodes = len(self.nodes)
    #     return [random.randrange(nb_nodes) for _ in range(self.nb_genes)]

    # def gen_init_population(self):
    #     pop = [[i] * self.nb_genes for i in range(len(self.nodes))]
    #     return pop

    def gen_rand_individual(self):
        nb_apps = len(self.apps)
        r_apps = range(nb_apps)
        nb_nodes = len(self.nodes)
        r_nodes = range(nb_nodes)

        app_nodes = [random.sample(r_nodes, self.apps[a][MAX_INSTANCES])
                     for a in r_apps]
        indiv = [random.choice(app_nodes[r[0]]) for r in self.requests]
        return indiv

    def gen_init_population(self):
        cloud = len(self.nodes) - 1
        indiv = [cloud for _ in range(self.nb_genes)]
        return [indiv]

    def crossover(self, indiv_1, indiv_2, prob_1, prob_2):
        offsprings = SP_Chromosome.crossover(self, indiv_1, indiv_2, prob_1, prob_2)
        return list(map(lambda i: self._cross_repair(i), offsprings))

    def _cross_repair(self, individual):
        nb_apps = len(self.apps)
        r_apps = range(nb_apps)
        nb_nodes = len(self.nodes)
        r_nodes = range(nb_nodes)
        r_requests = range(len(self.requests))

        instances = [[0 for _ in r_nodes] for _ in r_apps]
        remap = {(a, h): h for h in r_nodes for a in r_apps}

        for r in r_requests:
            h = individual[r]
            a, b = self.requests[r]
            instances[a][h] = 1

        for a in r_apps:
            exceeded = sum(instances[a]) - self.apps[a][MAX_INSTANCES]
            if exceeded > 0:
                nodes = list(filter(lambda h: instances[a][h] > 0, r_nodes))
                random.shuffle(nodes)
                removed = nodes[:exceeded]
                nodes = nodes[exceeded:]
                for old_h in removed:
                    new_h = random.choice(nodes)
                    remap[(a, old_h)] = new_h

        for r in r_requests:
            old_h = individual[r]
            a, b = self.requests[r]
            new_h = remap[(a, old_h)]
            individual[r] = new_h

        return individual

    def fitness(self, individual):
        result = self.decode(individual)

        viol_instances = self._calc_instances_violation(*result)
        viol_nodes = self._calc_nodes_violation(*result)

        nb_violations = viol_instances + viol_nodes
        if nb_violations == 0:
            return self.metric.get_qos_violation(*result)
        else:
            return VIOL_PENALITY * nb_violations

    def _calc_instances_violation(self, place, load):
        r_apps = range(len(self.apps))
        r_nodes = range(len(self.nodes))

        viol_instances = 0
        for a in r_apps:
            nb_instances = sum([place[a, h] for h in r_nodes])
            if nb_instances > self.apps[a][MAX_INSTANCES] or nb_instances == 0:
                viol_instances += 1

        return viol_instances

    def _calc_nodes_violation(self, place, load):
        r_apps = range(len(self.apps))
        r_nodes = range(len(self.nodes))

        viol_nodes = 0
        for h in r_nodes:
            violated = False
            for r in self.resources:
                demand = 0
                for a in r_apps:
                    k1 = self.demand[a][r][K1]
                    k2 = self.demand[a][r][K2]
                    node_load = int(sum([load[a, b, h] for b in r_nodes]))
                    demand += float(place[a, h] * (node_load * k1 + k2))
                if demand > self.nodes[h][r]:
                    violated = True
                    break
            if violated:
                viol_nodes += 1

        return viol_nodes

    def decode(self, individual):
        r_apps = range(len(self.apps))
        r_nodes = range(len(self.nodes))
        r_requests = range(len(self.requests))

        place = {(a, h): 0
                 for h in r_nodes
                 for a in r_apps}
        load = {(a, b, h): 0
                for h in r_nodes
                for b in r_nodes
                for a in r_apps}

        for r in r_requests:
            a, b = self.requests[r]
            h = individual[r]
            place[a, h] = 1
            load[a, b, h] += 1

        # return self.local_search(place, load)
        return place, load


def solve_sp(input,
             nb_generations=200,
             population_size=200,
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
    result = chromossome.decode(population[0])
    return Output(input).set_solution(*result)
