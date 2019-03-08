from algo.util.output import Output
from algo.util.nsgaii import NSGAII, NSGAII_Chromosome
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
                 population_size,
                 nb_generations,
                 elite_proportion,
                 mutant_proportion):

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
        result = self.decode(individual)
        return [self.metric.get_qos_violation(*result),
                self.metric.get_resource_wastage(*result),
                self.metric.get_active_nodes(*result),
                self.metric.get_cpu_consumption(*result),
                self.metric.get_avg_qos_violation(*result)]


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
    result = chromossome.decode(population[0])
    return Output(input).set_solution(*result)
