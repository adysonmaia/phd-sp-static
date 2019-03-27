from functools import cmp_to_key
from algo.util.brkga import BRKGA, Chromosome

INF = float("inf")


class NSGAII(BRKGA):
    def __init__(self,
                 chromossome,
                 population_size,
                 nb_generations,
                 elite_proportion,
                 mutant_proportion):

        BRKGA.__init__(self, chromossome, population_size, nb_generations,
                       elite_proportion, mutant_proportion)

    def _classify_population(self, population):
        fitnesses = [self.chromossome.fitness(i) for i in population]
        fronts, rank = self._fast_non_dominated_sort(fitnesses)
        distances = self._crowding_distance(fitnesses, fronts)

        def sort_cmp(indiv_1, indiv_2):
            index_1 = population.index(indiv_1)
            index_2 = population.index(indiv_2)
            if rank[index_1] < rank[index_2]:
                return -1
            elif (rank[index_1] == rank[index_2]) and (distances[index_1] < distances[index_2]):
                return -1
            else:
                return 1

        return sorted(population, key=cmp_to_key(sort_cmp))

    def _dominates(self, fitness_1, fitness_2):
        dominates = False
        for i in range(len(fitness_1)):
            if fitness_1[i] > fitness_2[i]:
                return False
            elif fitness_1[i] < fitness_2[i]:
                dominates = True

        return dominates

    def _fast_non_dominated_sort(self, fitnesses):
        pop_size = len(fitnesses)
        r_pop_size = range(pop_size)
        S = [[] for _ in r_pop_size]
        n = [0 for _ in r_pop_size]
        rank = [0 for _ in r_pop_size]
        fronts = [[]]

        for p in r_pop_size:
            S[p] = []
            n[p] = 0
            for q in r_pop_size:
                if self._dominates(fitnesses[p], fitnesses[q]):
                    if q not in S[p]:
                        S[p].append(q)
                elif self._dominates(fitnesses[q], fitnesses[p]):
                    n[p] = n[p] + 1
            if n[p] == 0:
                rank[p] = 0
                if p not in fronts[0]:
                    fronts[0].append(p)

        i = 0
        while(fronts[i] != []):
            Q = []
            for p in fronts[i]:
                for q in S[p]:
                    n[q] = n[q] - 1
                    if n[q] == 0:
                        rank[q] = i + 1
                        if q not in Q:
                            Q.append(q)
            i = i + 1
            fronts.append(Q)

        del fronts[len(fronts) - 1]
        return fronts, rank

    def _crowding_distance(self, fitnesses, fronts):
        nb_obj = len(fitnesses[0])
        distances = [0 for _ in range(len(fitnesses))]

        for front in fronts:
            for m in range(nb_obj):
                sorted = list(front)
                sorted.sort(key=lambda p: fitnesses[p][m])
                distances[0] = distances[len(front) - 1] = INF

                values = [value[m] for value in fitnesses]
                min_value = float(min(values))
                max_value = float(max(values))

                if max_value != min_value:
                    for i in range(1, len(front) - 1):
                        distances[sorted[i]] += (values[sorted[i + 1]] - values[sorted[i - 1]]) / (max_value - min_value)

        return distances


class NSGAII_Chromosome(Chromosome):
    def __init__(self):
        Chromosome.__init__(self)

    def stopping_criteria(self, population):
        return False

    def fitness(self, individual):
        return [0.0]
