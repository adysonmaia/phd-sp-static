from algo.util.output import Output
from algo.util.nsgaii import NSGAII, NSGAII_Chromosome
from algo.genetic import SP_Chromosome

DOMINANCE_ERROR = 0.01
STOP_THRESHOLD = 0.10
POOL_SIZE = 4


class SP_NSGAII(NSGAII):
    def __init__(self,
                 chromossome,
                 population_size,
                 nb_generations,
                 elite_proportion,
                 mutant_proportion,
                 elite_probability,
                 pool_size,
                 stop_threshold,
                 dominance_error):

        NSGAII.__init__(self, chromossome, population_size, nb_generations,
                        elite_proportion, mutant_proportion, elite_probability,
                        pool_size, stop_threshold)
        self.dominance_error = dominance_error

    def _dominates(self, fitness_1, fitness_2):
        if len(fitness_1) > 1 and abs(fitness_1[0] - fitness_2[0]) <= self.dominance_error:
            return NSGAII._dominates(self, fitness_1[1:], fitness_2[1:])
        else:
            return fitness_1[0] < fitness_2[0]


class MO_Chromosome(SP_Chromosome, NSGAII_Chromosome):
    def __init__(self, input, objectives=None, use_heuristic=True):
        NSGAII_Chromosome.__init__(self)
        SP_Chromosome.__init__(self, input, use_heuristic=use_heuristic)
        if objectives is None:
            objectives = [
                self.metric.get_max_deadline_violation,
                self.metric.get_cost,
                self.metric.get_avg_unavailability
            ]
        self.objectives = objectives

    def stopping_criteria(self, population):
        return False

    def fitness(self, individual):
        solution = self.decode(individual)
        return [f(*solution) for f in self.objectives]


def solve(input,
          nb_generations=100,
          population_size=100,
          elite_proportion=0.1,
          mutant_proportion=0.1,
          elite_probability=0.6,
          dominance_error=DOMINANCE_ERROR,
          stop_threshold=STOP_THRESHOLD,
          objective=None,
          use_heuristic=True,
          pool_size=POOL_SIZE):

    chromossome = MO_Chromosome(input, objective, use_heuristic=use_heuristic)
    genetic = SP_NSGAII(chromossome,
                        nb_generations=nb_generations,
                        population_size=population_size,
                        elite_proportion=elite_proportion,
                        mutant_proportion=mutant_proportion,
                        elite_probability=elite_probability,
                        stop_threshold=stop_threshold,
                        pool_size=pool_size,
                        dominance_error=dominance_error)

    population = genetic.solve()
    result = chromossome.decode(population[0])
    return Output(input).set_solution(*result)
