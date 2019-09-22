from functools import cmp_to_key
from algo.util.brkga import BRKGA, Chromosome


INF = float("inf")
MAX_CRWD_DIST = 1.0
# MAX_CRWD_DIST = INF


# Non-dominated Sorting Genetic Algorithm II
class NSGAII(BRKGA):
    def __init__(self,
                 chromossome,
                 population_size,
                 nb_generations,
                 elite_proportion,
                 mutant_proportion,
                 elite_probability,
                 pool_size=0,
                 stop_threshold=0.0):

        BRKGA.__init__(self, chromossome, population_size, nb_generations,
                       elite_proportion, mutant_proportion, elite_probability,
                       pool_size)
        self.stop_threshold = stop_threshold

    def _init_params(self):
        BRKGA._init_params(self)
        self._previous_nd_fitness = None
        self._current_nd_fitness = None
        self._mgbm_estimation = 1
        self._mgbm_count = 0

    def _stopping_criteria(self, population):
        return (self.chromossome.stopping_criteria(population)
                or self._stopping_criteria_mgbm())

    def _stopping_criteria_mgbm(self):
        """Calculate the MGBM stopping criteria
        based on Mutual Domination Rate (MDR) indicator
        and a simplified Kalman filter
        See also:
        https://doi.org/10.1016/j.ins.2016.07.025
        """
        self._mgbm_count += 1
        if self._previous_nd_fitness:
            prev_fitnesses = self._previous_nd_fitness
            curr_fitnesses = self._current_nd_fitness

            prev_count = 0
            curr_count = 0
            for prev_fit in prev_fitnesses:
                for curr_fit in curr_fitnesses:
                    if self._dominates(curr_fit, prev_fit):
                        prev_count += 1
                        break

            for curr_fit in curr_fitnesses:
                for prev_fit in prev_fitnesses:
                    if self._dominates(prev_fit, curr_fit):
                        curr_count += 1
                        break

            mdr = (prev_count / float(len(prev_fitnesses))
                   - curr_count / float(len(curr_fitnesses)))

            t = self._mgbm_count
            i = self._mgbm_estimation
            i = (t / float(t + 1)) * i + (1 / float(t + 1)) * mdr
            self._mgbm_estimation = i
            # print("{}\t{}\t{}".format(t, mdr, i))

        return self._mgbm_estimation < self.stop_threshold

    def _classify_population(self, population):
        fitnesses = self._get_fitnesses(population)
        fronts, rank = self._fast_non_dominated_sort(fitnesses)
        crwd_dist = self._crowding_distance(fitnesses, fronts)

        self._previous_nd_fitness = self._current_nd_fitness
        self._current_nd_fitness = list(map(lambda i: fitnesses[i], fronts[0]))

        def sort_cmp(indiv_1, indiv_2):
            index_1 = population.index(indiv_1)
            index_2 = population.index(indiv_2)
            if rank[index_1] < rank[index_2]:
                return -1
            elif (rank[index_1] == rank[index_2]
                  and crwd_dist[index_1] < crwd_dist[index_2]):
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

        normalize = []
        for m in range(nb_obj):
            values = [value[m] for value in fitnesses]
            min_value = min(values)
            max_value = max(values)
            normalize.append(float(max_value - min_value))

        for front in fronts:
            for m in range(nb_obj):
                sorted = list(front)
                sorted.sort(key=lambda p: fitnesses[p][m])
                distances[sorted[0]] = distances[sorted[-1]] = MAX_CRWD_DIST

                if normalize[m] > 0.0:
                    for i in range(1, len(sorted) - 1):
                        value_previous = fitnesses[sorted[i - 1]][m]
                        value_next = fitnesses[sorted[i + 1]][m]
                        value_diff = value_next - value_previous
                        distances[sorted[i]] += value_diff / normalize[m]

        return distances


class NSGAII_Chromosome(Chromosome):
    def __init__(self):
        Chromosome.__init__(self)

    def stopping_criteria(self, population):
        return False

    def fitness(self, individual):
        return [0.0]
