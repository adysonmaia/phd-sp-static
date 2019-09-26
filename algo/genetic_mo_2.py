from algo.util.output import Output
from algo.util.nsgaii import NSGAII
from algo.genetic_mo import MO_Chromosome

POOL_SIZE = 4


def solve(input,
          nb_generations=100,
          population_size=100,
          elite_proportion=0.1,
          mutant_proportion=0.2,
          elite_probability=0.6,
          stop_threshold=0.10,
          objective=None,
          pool_size=POOL_SIZE):

    chromossome = MO_Chromosome(input, objective)
    genetic = NSGAII(chromossome,
                     nb_generations=nb_generations,
                     population_size=population_size,
                     elite_proportion=elite_proportion,
                     mutant_proportion=mutant_proportion,
                     elite_probability=elite_probability,
                     stop_threshold=stop_threshold,
                     pool_size=pool_size)

    population = genetic.solve()
    result = chromossome.decode(population[0])
    return Output(input).set_solution(*result)
