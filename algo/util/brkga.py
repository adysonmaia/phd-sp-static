import random
# from pathos.threading import ThreadPool
from pathos.multiprocessing import ProcessPool
# from pool import ThreadPool


# BiasedRandomKeyGeneticAlgorithm
class BRKGA:
    def __init__(self,
                 chromossome,
                 population_size,
                 nb_generations,
                 elite_proportion,
                 mutant_proportion,
                 pool_size=0):

        self.chromossome = chromossome
        self.nb_genes = chromossome.nb_genes
        self.pop_size = population_size
        self.nb_generations = nb_generations
        self.elite_proportion = elite_proportion
        self.mutant_proportion = mutant_proportion
        self._elite_size = int(round(self.elite_proportion * self.pop_size))
        self._mutant_size = int(round(self.mutant_proportion * self.pop_size))

        if pool_size > 0:
            self._pool = ProcessPool(pool_size)
        else:
            self._pool = None

    def _stopping_criteria(self, population):
        return self.chromossome.stopping_criteria(population)

    def _gen_rand_individual(self):
        return self.chromossome.gen_rand_individual()

    def _crossover(self, indiv_1, indiv_2, prob_1, prob_2):
        return self.chromossome.crossover(indiv_1, indiv_2, prob_1, prob_2)

    def _set_fitness(self, individual):
        if len(individual) == self.nb_genes:
            value = self.chromossome.fitness(individual)
            individual.append(value)
        return individual

    def _classify_population(self, population):
        map_func = map
        if self._pool:
            map_func = self._pool.map

        population = list(map_func(self._set_fitness, population))
        population.sort(key=lambda indiv: indiv[self.nb_genes])
        return population

    def _gen_first_population(self):
        pop = list(self.chromossome.gen_init_population())

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
        try:
            for i in range(self.nb_generations):
                if self._stopping_criteria(pop):
                    break
                pop = self._gen_next_population(pop)
        except KeyboardInterrupt:
            raise
        finally:
            return pop


class Chromosome():
    def __init__(self):
        self.nb_genes = 1

    def gen_rand_individual(self):
        return [random.random() for _ in range(self.nb_genes)]

    def gen_init_population(self):
        return []

    def crossover(self, indiv_1, indiv_2, prob_1, prob_2):
        if prob_1 < prob_2:
            indiv_1, indiv_2 = indiv_2, indiv_1
            prob_1, prob_2 = prob_2, prob_1

        offspring_1 = indiv_1[:self.nb_genes]

        for g in range(self.nb_genes):
            if random.random() < prob_1:
                offspring_1[g] = indiv_2[g]

        return [offspring_1]

    def stopping_criteria(self, population):
        return False

    def fitness(self, individual):
        return 0.0
