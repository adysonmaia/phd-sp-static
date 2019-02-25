from nsgaii import NSGAII, NSGAII_Chromosome
from genetic_2 import SP2_Chromosome

INF = float("inf")
POOL_SIZE = 0
K1 = 0
K2 = 1
CPU = "CPU"
DEADLINE = "deadline"
MAX_INSTANCES = "max_instances"
REQUEST_RATE = "request_rate"
WORK_SIZE = "work_size"


class MO_Chromosome(SP2_Chromosome, NSGAII_Chromosome):
    def __init__(self, input):
        NSGAII_Chromosome.__init__(self)
        SP2_Chromosome.__init__(self, input)

    def stopping_criteria(self, population):
        return False

    def fitness(self, individual):
        data_decoded = self.decode(individual)
        return [self.calc_qos_violation(*data_decoded)]


def solve_sp(input,
             nb_generations=200,
             population_size=100,
             elite_proportion=0.4,
             mutant_proportion=0.3):

    chromossome = MO_Chromosome(input)
    genetic = NSGAII(chromossome,
                     nb_generations=nb_generations,
                     population_size=population_size,
                     elite_proportion=elite_proportion,
                     mutant_proportion=mutant_proportion)

    population = genetic.solve()

    data_decoded = chromossome.decode(population[0])
    e = chromossome.calc_qos_violation(*data_decoded)
    place = chromossome.get_places(*data_decoded)
    distribution = chromossome.get_distributions(*data_decoded)

    return e, place, distribution
