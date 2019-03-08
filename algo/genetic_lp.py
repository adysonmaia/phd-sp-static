import math
from docplex.mp.model import Model
from algo.util.output import Output
from algo.util.brkga import BRKGA
from algo.genetic import SP_Chromosome


INF = float("inf")
POOL_SIZE = 3
K1 = 0
K2 = 1
E_MAX = 1000.0
CPLEX_TIME_LIMIT = 10
CPU = "CPU"
DEADLINE = "deadline"
MAX_INSTANCES = "max_instances"
REQUEST_RATE = "request_rate"
WORK_SIZE = "work_size"


class LP_Chromosome(SP_Chromosome):
    def __init__(self, input):
        SP_Chromosome.__init__(self, input)
        self.nb_genes = len(self.apps) * len(self.nodes)

    def gen_init_population(self):
        return []

    def decode(self, individual):
        nb_apps = len(self.apps)
        r_apps = range(nb_apps)
        nb_nodes = len(self.nodes)
        r_nodes = range(nb_nodes)
        cloud = nb_nodes - 1

        place = {(a, h): 0
                 for h in r_nodes
                 for a in r_apps}

        for a in r_apps:
            start = a * nb_nodes
            end = start + nb_nodes + 1
            priority = individual[start:end]
            nodes_priority = list(r_nodes)
            nodes_priority.sort(key=lambda h: priority[h], reverse=True)
            max_nodes = min(nb_nodes, self.apps[a][MAX_INSTANCES])
            nodes_selected = nodes_priority[:max_nodes]

            place[a, cloud] = 1
            for h in nodes_selected:
                place[a, h] = 1

        # start_time = time.time()
        load = self._decode_load_distribution(place)
        # elapsed_time = time.time() - start_time
        # print("load distri time: {}".format(elapsed_time))
        return self.local_search(place, load)

    def _decode_load_distribution(self, place):
        nb_apps = len(self.apps)
        r_apps = range(nb_apps)
        nb_nodes = len(self.nodes)
        r_nodes = range(nb_nodes)

        requests = [[int(math.ceil(self.users[a][b] * self.apps[a][REQUEST_RATE]))
                     for b in r_nodes]
                    for a in r_apps]
        max_load = [sum(requests[a]) for a in r_apps]

        mdl = Model(name='ServicePlacement')

        # Decision Variables
        dvar_distribution = mdl.continuous_var_cube(nb_apps, nb_nodes, nb_nodes,
                                                    lb=0, name="d")
        dvar_e = mdl.continuous_var(lb=0, ub=E_MAX, name="e")
        dvar_ld = mdl.continuous_var_cube(nb_apps, nb_nodes, nb_nodes, lb=0.0, name="ld")

        # Decision Expresions
        dexpr_load = {(a, h): mdl.sum(dvar_distribution[a, b, h] for b in r_nodes)
                      for a in r_apps
                      for h in r_nodes}

        # Constraints
        # Request Flow Existance
        mdl.add_constraints(dvar_distribution[a, b, h]
                            <= place[a, h] * requests[a][b]
                            for a in r_apps
                            for b in r_nodes
                            for h in r_nodes)
        # Load Conservation
        mdl.add_constraints(mdl.sum(dvar_distribution[a, b, h] for h in r_nodes)
                            == requests[a][b]
                            for a in r_apps
                            for b in r_nodes)
        # Node Capacity
        mdl.add_constraints(mdl.sum((dexpr_load[a, h] * self.demand[a][r][K1]
                                     + self.demand[a][r][K2]) * place[a, h]
                                    for a in r_apps)
                            <= self.nodes[h][r]
                            for h in r_nodes
                            for r in self.resources)
        # QoS Violation
        cpu_k1 = [self.demand[a][CPU][K1] for a in r_apps]
        cpu_k2 = [self.demand[a][CPU][K2] for a in r_apps]
        work_size = [self.apps[a][WORK_SIZE] for a in r_apps]
        deadline = [self.apps[a][DEADLINE] for a in r_apps]
        net_delay = self.net_delay
        mdl.add_constraints(dvar_ld[a, b, h] * (cpu_k1[a] - work_size[a]) * (net_delay[a][b][h] - deadline[a])
                            + dvar_distribution[a, b, h] * (cpu_k2[a] * (net_delay[a][b][h] - deadline[a]) + work_size[a])
                            <= dvar_e
                            for a in r_apps
                            for b in r_nodes
                            for h in r_nodes)
        # Linearization of Bilinear Term 1
        mdl.add_constraints(dvar_ld[a, b, h]
                            >= max_load[a] * dvar_distribution[a, b, h]
                            + requests[a][b] * dexpr_load[a, h]
                            - requests[a][b] * max_load[a]
                            for a in r_apps
                            for b in r_nodes
                            for h in r_nodes)
        mdl.add_constraints(dvar_ld[a, b, h] <= max_load[a] * dvar_distribution[a, b, h]
                            for a in r_apps
                            for b in r_nodes
                            for h in r_nodes)
        mdl.add_constraints(dvar_ld[a, b, h] <= requests[a][b] * dexpr_load[a, h]
                            for a in r_apps
                            for b in r_nodes
                            for h in r_nodes)

        # Search space reduction
        # for a in r_apps:
        #     for b in range(nb_nodes - 2):
        #         for h in range(nb_nodes - 2):
        #             if self.net_delay[a][b][h] > self.apps[a][DEADLINE]:
        #                 mdl.add_constraint(dvar_distribution[a, b, h] == 0)

        # Objective
        mdl.minimize(dvar_e)

        mdl.context.cplex_parameters.timelimit = CPLEX_TIME_LIMIT
        # mdl.print_information()
        if mdl.solve():
            load = {(a, b, h): dvar_distribution[a, b, h].solution_value
                    for h in r_nodes
                    for b in r_nodes
                    for a in r_apps}
        else:
            cloud = nb_nodes - 1
            load = {(a, b, h): 0 if h != cloud else requests[a][b]
                    for a in r_apps
                    for b in r_nodes
                    for h in r_nodes}
        return load

    def local_search(self, place, load):
        nb_apps = len(self.apps)
        r_apps = range(nb_apps)
        nb_nodes = len(self.nodes)
        r_nodes = range(nb_nodes)
        cloud = nb_nodes - 1

        # TODO improve this
        for a in r_apps:
            for b in r_nodes:
                requests = int(math.ceil(self.users[a][b] * self.apps[a][REQUEST_RATE]))
                for h in r_nodes:
                    load[a, b, h] = int(round(load[a, b, h]))
                load_ab = sum(load[a, b, h] for h in r_nodes)
                if load_ab != requests:
                    # print("app {} - source {}: load {} - requests {}".format(a, b, load_ab, requests))
                    load[a, b, cloud] += requests - load_ab

        return SP_Chromosome.local_search(self, place, load)


def solve_sp(input,
             nb_generations=10,
             population_size=10,
             elite_proportion=0.4,
             mutant_proportion=0.3):

    chromossome = LP_Chromosome(input)
    genetic = BRKGA(chromossome,
                    nb_generations=nb_generations,
                    population_size=population_size,
                    elite_proportion=elite_proportion,
                    mutant_proportion=mutant_proportion,
                    pool_size=POOL_SIZE)

    population = genetic.solve()
    result = chromossome.decode(population[0])
    return Output(input).set_solution(*result)
