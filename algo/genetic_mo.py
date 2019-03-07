from algo.nsgaii import NSGAII, NSGAII_Chromosome
from algo.genetic_2 import SP2_Chromosome

INF = float("inf")
POOL_SIZE = 0
K1 = 0
K2 = 1
CPU = "CPU"
DEADLINE = "deadline"
MAX_INSTANCES = "max_instances"
REQUEST_RATE = "request_rate"
WORK_SIZE = "work_size"


class SP_NSGAII(NSGAII):
    def __init__(self,
                 chromossome,
                 population_size=100,
                 nb_generations=100,
                 elite_proportion=0.5,
                 mutant_proportion=0.1):

        NSGAII.__init__(self, chromossome, population_size, nb_generations,
                        elite_proportion, mutant_proportion)

    def _dominates(self, fitness_1, fitness_2):
        if abs(fitness_1[0] - fitness_2[0]) <= 0.1:
            return NSGAII._dominates(self, fitness_1[1:], fitness_2[1:])
        else:
            return fitness_1[0] < fitness_2[0]


class MO_Chromosome(SP2_Chromosome, NSGAII_Chromosome):
    def __init__(self, input):
        NSGAII_Chromosome.__init__(self)
        SP2_Chromosome.__init__(self, input)

    def stopping_criteria(self, population):
        return False

    def fitness(self, individual):
        data_decoded = self.decode(individual)
        return [self.calc_qos_violation(*data_decoded),
                self.calc_wastage(*data_decoded),
                self.calc_active_nodes(*data_decoded),
                self.calc_cpu_consumption(*data_decoded),
                self.calc_avg_qos_violation(*data_decoded)]

    def calc_wastage(self, place, load):
        r_apps = range(len(self.apps))
        r_nodes = range(len(self.nodes))

        wastage = 0
        for h in r_nodes:
            for r in self.resources:
                capacity = float(self.nodes[h][r])
                if capacity == 0.0 or capacity == INF:
                    continue
                used = 0
                for a in r_apps:
                    app_load = sum([load[a, b, h] for b in r_nodes])
                    r_k1 = self.demand[a][r][K1]
                    r_k2 = self.demand[a][r][K2]
                    used += place[a, h] * (r_k1 * app_load + r_k2)
                wastage += (capacity - used) / capacity
        return wastage

    def calc_active_nodes(self, place, load):
        r_apps = range(len(self.apps))
        r_nodes = range(len(self.nodes))

        count = 0
        for h in r_nodes:
            instances = sum([place[a, h] for a in r_apps])
            if instances > 0:
                count += 1
        return count

    def calc_cpu_consumption(self, place, load):
        r_apps = range(len(self.apps))
        r_nodes = range(len(self.nodes))

        consumption = 0
        for h in r_nodes:
            capacity = float(self.nodes[h][CPU])
            if capacity == 0.0 or capacity == INF:
                continue
            used = 0
            for a in r_apps:
                app_load = sum([load[a, b, h] for b in r_nodes])
                cpu_k1 = self.demand[a][CPU][K1]
                cpu_k2 = self.demand[a][CPU][K2]
                used += place[a, h] * (cpu_k1 * app_load + cpu_k2)
            consumption += used / capacity
        return consumption

    def calc_avg_qos_violation(self, place, load):
        r_apps = range(len(self.apps))
        r_nodes = range(len(self.nodes))

        e = 0.0
        count = 0
        for a in r_apps:
            app = self.apps[a]
            work_size = app[WORK_SIZE]
            deadline = app[DEADLINE]
            cpu_k1 = self.demand[a][CPU][K1]
            cpu_k2 = self.demand[a][CPU][K2]

            instances = list(filter(lambda h: place[a, h] > 0, r_nodes))
            bs = list(filter(lambda b: self.users[a][b] > 0, r_nodes))

            for h in instances:
                node_load = sum([load[a, b, h] for b in bs])
                if node_load == 0.0:
                    continue
                proc_delay_divisor = float(node_load * (cpu_k1 - work_size) + cpu_k2)
                proc_delay = INF
                if proc_delay_divisor > 0.0:
                    proc_delay = app[WORK_SIZE] / proc_delay_divisor
                for b in bs:
                    if load[a, b, h] > 0:
                        delay = self.net_delay[a][b][h] + proc_delay
                        if delay > deadline:
                            e += delay - deadline
                            count += 1
        if count > 0:
            return e / float(count)
        else:
            return 0.0


def solve_sp(input,
             nb_generations=200,
             population_size=100,
             elite_proportion=0.4,
             mutant_proportion=0.3):

    chromossome = MO_Chromosome(input)
    # genetic = NSGAII(chromossome,
    #                  nb_generations=nb_generations,
    #                  population_size=population_size,
    #                  elite_proportion=elite_proportion,
    #                  mutant_proportion=mutant_proportion)

    genetic = SP_NSGAII(chromossome,
                        nb_generations=nb_generations,
                        population_size=population_size,
                        elite_proportion=elite_proportion,
                        mutant_proportion=mutant_proportion)

    population = genetic.solve()

    data_decoded = chromossome.decode(population[0])
    e = chromossome.calc_qos_violation(*data_decoded)
    place = chromossome.get_places(*data_decoded)
    distribution = chromossome.get_distributions(*data_decoded)

    print(chromossome.fitness(population[0]))

    return e, place, distribution
