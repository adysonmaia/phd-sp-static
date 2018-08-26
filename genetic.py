import random
import math
from pathos.multiprocessing import ProcessPool

INF = float("inf")
POOL_SIZE = 0
K1 = 0
K2 = 1
CPU = "CPU"
DEADLINE = "deadline"
MAX_INSTANCES = "max_instances"
REQUEST_RATE = "request_rate"
WORK_SIZE = "work_size"


class BiasedRandomKeyGenetic:

    def __init__(self,
                 nb_genes,
                 fitness_func,
                 stopping_func=None,
                 population_size=100,
                 nb_generations=100,
                 elite_proportion=0.5,
                 mutant_proportion=0.1,
                 initial_population=[],
                 pool_size=0):

        self.nb_genes = nb_genes
        self.fitness = fitness_func
        self.stopping_criteria = stopping_func
        self.pop_size = population_size
        self.nb_generations = nb_generations
        self.elite_proportion = elite_proportion
        self.mutant_proportion = mutant_proportion
        self._elite_size = int(round(self.elite_proportion * self.pop_size))
        self._mutant_size = int(round(self.mutant_proportion * self.pop_size))
        self.initial_population = initial_population

        if pool_size > 0:
            self._pool = ProcessPool(pool_size)
        else:
            self._pool = None

    def _gen_rand_individual(self):
        return [random.random() for g in range(self.nb_genes)]

    # def _crossover(self, indiv_1, indiv_2, prob_1, prob_2):
    #     if prob_1 < prob_2:
    #         indiv_1, indiv_2 = indiv_2, indiv_1
    #         prob_1, prob_2 = prob_2, prob_1
    #
    #     offspring_1 = indiv_1[:]
    #     offspring_2 = indiv_2[:]
    #
    #     for g in range(self.nb_genes):
    #         if random.random() < prob_1:
    #             offspring_1[g] = indiv_2[g]
    #         else:
    #             offspring_2[g] = indiv_1[g]
    #
    #     return [offspring_1, offspring_2]

    def _crossover(self, indiv_1, indiv_2, prob_1, prob_2):
        if prob_1 < prob_2:
            indiv_1, indiv_2 = indiv_2, indiv_1
            prob_1, prob_2 = prob_2, prob_1

        offspring_1 = indiv_1[:]

        for g in range(self.nb_genes):
            if random.random() < prob_1:
                offspring_1[g] = indiv_2[g]

        return [offspring_1]

    def _set_fitness(self, individual):
        if len(individual) == self.nb_genes:
            value = self.fitness(individual)
            individual.append(value)
        return individual

    def _classify_population(self, population):
        map_func = map
        if self._pool:
            map_func = self._pool.map

        population = map_func(self._set_fitness, population)
        population.sort(key=lambda indiv: indiv[self.nb_genes])
        return population

    def _gen_first_population(self):
        pop = self.initial_population[:]

        rand_size = self.pop_size - len(pop)
        if rand_size > 0:
            pop += [self._gen_rand_individual()
                    for i in range(rand_size)]

        return self._classify_population(pop)

    def _gen_next_population(self, prev_ranked_pop):
        next_population = []

        elite = prev_ranked_pop[:self._elite_size]
        next_population += elite

        mutants = [self._gen_rand_individual()
                   for i in range(self._mutant_size)]
        next_population += mutants

        non_elite = prev_ranked_pop[self._elite_size:]
        non_elite_size = len(non_elite)
        cross_size = self.pop_size - self._elite_size - self._mutant_size
        for i in range(cross_size):
            indiv_1 = random.choice(elite)
            indiv_2 = random.choice(non_elite)
            offspring = self._crossover(indiv_1, indiv_2,
                                        self._elite_size / float(self.pop_size),
                                        non_elite_size / float(self.pop_size))
            next_population += offspring

        next_population = self._classify_population(next_population)
        return next_population[:self.pop_size]

    def solve(self):
        self._elite_size = int(round(self.elite_proportion * self.pop_size))
        self._mutant_size = int(round(self.mutant_proportion * self.pop_size))
        pop = self._gen_first_population()
        for i in range(self.nb_generations):
            if self.stopping_criteria and self.stopping_criteria(pop):
                break
            pop = self._gen_next_population(pop)
        return pop


class SP_Chromosome:

    def __init__(self,
                 nodes,
                 apps,
                 users,
                 resources,
                 net_delay,
                 demand):

        self.nodes = nodes
        self.apps = apps
        self.users = users
        self.resources = resources
        self.net_delay = net_delay
        self.demand = demand

        self.nb_genes = len(apps) * (2 * len(nodes) + 1)

    def gen_init_population(self):
        nb_apps = len(self.apps)
        r_apps = range(nb_apps)
        nb_nodes = len(self.nodes)
        r_nodes = range(nb_nodes)

        indiv = [0.0 for g in range(self.nb_genes)]

        count = 0
        total = float(nb_apps * nb_nodes)
        r_apps.sort(key=lambda a: self.apps[a][DEADLINE])
        for a in r_apps:
            r_nodes.sort(key=lambda b: self.users[a][b], reverse=True)
            for b in r_nodes:
                indiv[a*nb_nodes + b] = (total - count) / total
                count += 1

        return [indiv]

    def stopping_criteria(self, population):
        best_indiv = population[0]
        best_value = best_indiv[self.nb_genes]
        return best_value == 0.0

    def fitness(self, individual):
        data_decoded = self.decode(individual)
        return self.calc_qos_violation(*data_decoded)

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

            nodes_priority = r_nodes[:]
            nodes_priority.sort(key=lambda h:
                                self._decode_node_priority(individual, a, b, h),
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

        return self._decode_local_search(place, load)

    def _decode_node_priority(self, individual, app, bs, node):
        nb_apps = len(self.apps)
        nb_nodes = len(self.nodes)

        cloud_delay = self.net_delay[app][bs][nb_nodes - 1]
        node_delay = self.net_delay[app][bs][node]
        delay = (cloud_delay - node_delay) / cloud_delay

        weight = round(individual[nb_apps * nb_nodes + app], 2)
        value = individual[nb_apps * (nb_nodes + 1) + app * nb_nodes + node]

        return weight * value + (1.0 - weight) * delay

    def _decode_local_search(self, place, load):
        r_apps = range(len(self.apps))
        nb_nodes = len(self.nodes)
        r_nodes = range(nb_nodes)
        cloud = nb_nodes - 1

        for a in r_apps:
            app = self.apps[a]
            instances = [h for h in r_nodes if place[a, h] > 0]
            if len(instances) <= app[MAX_INSTANCES]:
                continue

            if not place[a, cloud]:
                place[a, cloud] = 1
                instances.append(cloud)

            def node_load(h): return sum([load[a, b, h] for b in r_nodes])
            instances.sort(key=node_load, reverse=True)

            while len(instances) > app[MAX_INSTANCES]:
                h = instances.pop()
                if h == cloud:
                    instances.insert(0, cloud)
                    continue
                place[a, h] = 0
                for b in r_nodes:
                    load[a, b, cloud] += load[a, b, h]
                    load[a, b, h] = 0

        return place, load

    def calc_qos_violation(self, place, load):
        r_apps = range(len(self.apps))
        r_nodes = range(len(self.nodes))

        e = 0.0
        for a in r_apps:
            app = self.apps[a]
            work_size = app[WORK_SIZE]
            deadline = app[DEADLINE]
            cpu_k1 = self.demand[a][CPU][K1]
            cpu_k2 = self.demand[a][CPU][K2]

            instances = [h for h in r_nodes if place[a, h] > 0]
            bs = [b for b, nb_users in enumerate(self.users[a]) if nb_users > 0]

            max_delay = 0.0
            for h in instances:
                node_load = sum([load[a, b, h] for b in bs])
                proc_delay_divisor = float(node_load * (cpu_k1 - work_size) + cpu_k2)
                proc_delay = INF
                if proc_delay_divisor > 0.0:
                    proc_delay = app[WORK_SIZE] / proc_delay_divisor
                for b in bs:
                    if load[a, b, h] > 0:
                        delay = self.net_delay[a][b][h] + proc_delay
                        if delay > max_delay:
                            max_delay = delay

            violation = max_delay - deadline
            if violation > 0.0 and violation > e:
                e = violation
        return e

    def get_distributions(self, place, load):
        r_apps = range(len(self.apps))
        r_nodes = range(len(self.nodes))

        return {(a, b, h): place[a, h] * load[a, b, h]
                / math.ceil(self.users[a][b] * self.apps[a][REQUEST_RATE])
                for a in r_apps
                for b in r_nodes
                for h in r_nodes
                if load[a, b, h] > 0}

    def get_places(self, place, load=None):
        r_apps = range(len(self.apps))
        r_nodes = range(len(self.nodes))

        return [[h for h in r_nodes if place[a, h] > 0] for a in r_apps]


def solve_sp(nodes,
             apps,
             users,
             resources,
             net_delay,
             demand,
             nb_generations=100,
             population_size=100,
             elite_proportion=0.4,
             mutant_proportion=0.3):

    chromossome = SP_Chromosome(nodes, apps, users, resources, net_delay, demand)
    init_pop = chromossome.gen_init_population()
    genetic = BiasedRandomKeyGenetic(chromossome.nb_genes, chromossome.fitness,
                                     chromossome.stopping_criteria,
                                     nb_generations=nb_generations,
                                     population_size=population_size,
                                     elite_proportion=elite_proportion,
                                     mutant_proportion=mutant_proportion,
                                     initial_population=init_pop,
                                     pool_size=POOL_SIZE)

    population = genetic.solve()

    data_decoded = chromossome.decode(population[0])
    e = chromossome.calc_qos_violation(*data_decoded)
    place = chromossome.get_places(*data_decoded)
    distribution = chromossome.get_distributions(*data_decoded)

    return e, place, distribution
