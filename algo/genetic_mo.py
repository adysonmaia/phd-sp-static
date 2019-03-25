from algo.util.output import Output
from algo.util.nsgaii import NSGAII, NSGAII_Chromosome
from algo.genetic_2 import SP2_Chromosome

DOMINANCE_ERROR = 0.01


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
        if len(fitness_1) > 1 and abs(fitness_1[0] - fitness_2[0]) <= DOMINANCE_ERROR:
            return NSGAII._dominates(self, fitness_1[1:], fitness_2[1:])
        else:
            return fitness_1[0] < fitness_2[0]


class MO_Chromosome(SP2_Chromosome, NSGAII_Chromosome):
    def __init__(self, input, metrics_func=None):
        NSGAII_Chromosome.__init__(self)
        SP2_Chromosome.__init__(self, input)
        if metrics_func is None:
            self.fitness_func = [self.metric.get_max_deadline_violation,
                                 self.metric.get_max_resource_usage,
                                 self.metric.get_avg_response_time]
        else:
            self.fitness_func = metrics_func

    def stopping_criteria(self, population):
        return False

    def fitness(self, individual):
        solution = self.decode(individual)
        return [f(*solution) for f in self.fitness_func]


def solve_sp(input,
             nb_generations=200,
             population_size=200,
             elite_proportion=0.4,
             mutant_proportion=0.3,
             metrics_func=None):

    chromossome = MO_Chromosome(input, metrics_func)
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
