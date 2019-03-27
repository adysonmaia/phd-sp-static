from algo.util.output import Output
from algo.util.nsgaii import NSGAII
from algo.genetic_mo import MO_Chromosome


def solve(input,
          nb_generations=100,
          population_size=100,
          elite_proportion=0.4,
          mutant_proportion=0.3,
          objectives=None):

    chromossome = MO_Chromosome(input, objectives)
    genetic = NSGAII(chromossome,
                     nb_generations=nb_generations,
                     population_size=population_size,
                     elite_proportion=elite_proportion,
                     mutant_proportion=mutant_proportion)

    population = genetic.solve()
    result = chromossome.decode(population[0])
    return Output(input).set_solution(*result)
