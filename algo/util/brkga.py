import random
import multiprocessing as mp


def _init_pool(genetic_algo):
    """Initialize a sub-procress to calculate an individual fitness
    Args:
        genetic_algo (BRKGA): a genetic algorithm object
    """
    global _ga
    _ga = genetic_algo


def _get_fitness(indiv):
    """Calculate the fitness of an individual
    Args:
        indiv (list): indivual
    Returns:
        fitness: fitness value
    """
    global _ga
    return _ga._get_fitness(indiv)


class BRKGA:
    """ Biased Random Key Genetic Algorithm
    See also:
    https://link.springer.com/article/10.1007/s10732-010-9143-1
    """

    def __init__(self,
                 chromossome,
                 population_size,
                 nb_generations,
                 elite_proportion,
                 mutant_proportion,
                 elite_probability=None,
                 pool_size=0):
        """Initialize method
        Args:
            chromossome (Chromosome): chromossome representation object
            population_size (int): population size
            nb_generations (int): maximum number of generations
            elite_proportion (float): proportion of the number of elite
                                      individuals in the population,
                                      value in [0, 1]
            mutant_proportion (float): proportion of the number of mutant
                                       individuals in the population,
                                       value in [0, 1]
            elite_probability (float): probability of a elite gene to be
                                       selected during crossvers
            pool_size (int): number of processes for parallelisms
        """

        self.chromossome = chromossome
        self.nb_genes = chromossome.nb_genes
        self.pop_size = population_size
        self.nb_generations = nb_generations
        self.elite_proportion = elite_proportion
        self.mutant_proportion = mutant_proportion
        self._elite_size = int(round(self.elite_proportion * self.pop_size))
        self._mutant_size = int(round(self.mutant_proportion * self.pop_size))
        self.elite_probability = elite_probability

        if self.elite_probability is None:
            self.elite_probability = self._elite_size / float(self.pop_size)

        # Initialize parallelism pool
        self._pool = None
        self._map_func = map
        self._fitness_func = self._get_fitness
        if pool_size > 0:
            try:
                # Require UNIX fork to work
                mp_ctx = mp.get_context("fork")
                pool_size = min(pool_size, mp_ctx.cpu_count())
                self._pool = mp_ctx.Pool(processes=pool_size,
                                         initializer=_init_pool,
                                         initargs=[self])
                self._map_func = self._pool.map
                self._fitness_func = _get_fitness
            except ValueError:
                pass

    def _init_params(self):
        """Initialize parameters before starting the genetic algorithm
        """
        self._elite_size = int(round(self.elite_proportion * self.pop_size))
        self._mutant_size = int(round(self.mutant_proportion * self.pop_size))
        self.chromossome.init_params()

    def _stopping_criteria(self, population):
        """Verify whether the GA should stop or not
        Args:
            population (list): population of the current generation
        Returns:
            stop: a boolean value, True if algorithm should stop
        """
        return self.chromossome.stopping_criteria(population)

    def _gen_rand_individual(self):
        """Generate a random indivual
        Returns:
            indivual: a new random indivual
        """
        return self.chromossome.gen_rand_individual()

    def _crossover(self, indiv_1, indiv_2, prob_1, prob_2):
        """Create individuals through crossover operation
        Args:
            indiv_1 (list): firt individual
            indiv_2 (list): second individual
            prob_1 (float): value in [0, 1] is the probability of
                            an indiv_1 gene being chosen for the offspring
            prob_2 (float): value in [0, 1] is the probability of
                            an indiv_2 gene being chosen for the offspring
        Returns:
            offspring: list of offspring
        """
        return self.chromossome.crossover(indiv_1, indiv_2, prob_1, prob_2)

    def _get_fitness(self, individual):
        """Calculate an individual fitness
        Args:
            individual (list): individual
        Returns:
            fitness: fitness value
        """
        # Check if the fitness is cached
        if len(individual) > self.nb_genes:
            return individual[-1]
        return self.chromossome.fitness(individual)

    def _get_fitnesses(self, population):
        """Calculate the fitness of all indivuals in a population
        Args:
            population (list): population
        Returns:
            fitnesses: list of fitnesses of all indivuals
        """
        fitnesses = list(self._map_func(self._fitness_func, population))
        # cache the fitness value inside the individual
        for (index, indiv) in enumerate(population):
            value = fitnesses[index]
            if len(indiv) == self.nb_genes:
                indiv.append(value)
        return fitnesses

    def _classify_population(self, population):
        """Sorts individuals by their fitness value
        Args:
            population (list): list of individuals
        Returns:
            population: list of sorted individuals
        """
        self._get_fitnesses(population)
        population.sort(key=lambda indiv: indiv[-1])
        return population

    def _gen_first_population(self):
        """Generate the indivuals of the first generation
        """
        # Get boostrap individuals generated by the chromossome representation
        pop = list(self.chromossome.gen_init_population())

        # Complete the population with random individuals
        rand_size = self.pop_size - len(pop)
        if rand_size > 0:
            pop += [self._gen_rand_individual()
                    for i in range(rand_size)]

        return self._classify_population(pop)

    def _gen_next_population(self, current_ranked_pop):
        """Generate the next population
        through selection, crossover, mutation operations
        in the current population
        Args:
            current_ranked_pop (list): current sorted population
        Returns:
            next_population: list of individuals of the next population
        """
        next_population = []

        # Get elite individuals
        elite = current_ranked_pop[:self._elite_size]
        next_population += elite

        # Get mutant indivuals
        mutants = [self._gen_rand_individual()
                   for i in range(self._mutant_size)]
        next_population += mutants

        # Get indivuals by crossover operation
        non_elite = current_ranked_pop[self._elite_size:]
        cross_size = self.pop_size - self._elite_size - self._mutant_size
        for i in range(cross_size):
            indiv_1 = random.choice(elite)
            indiv_2 = random.choice(non_elite)
            offspring = self._crossover(indiv_1, indiv_2,
                                        self.elite_probability,
                                        1.0 - self.elite_probability)
            next_population += offspring

        # Select indivuals with best fitness for next generation
        next_population = self._classify_population(next_population)
        return next_population[:self.pop_size]

    def solve(self):
        """Execute the genetic algorithm
        """
        self._init_params()
        pop = self._gen_first_population()
        try:
            for i in range(self.nb_generations):
                if self._stopping_criteria(pop):
                    break
                pop = self._gen_next_population(pop)
        except KeyboardInterrupt:
            if self._pool:
                self._pool.terminate()
            raise
        finally:
            return pop


class Chromosome():
    """Abstract chromosome class
    It is used to implement the decoding algorithm of BRKGA
    for a specific problem
    """

    def __init__(self):
        """Object initilization
        """
        self.nb_genes = 1

    def init_params(self):
        """Initialize parameters before starting the genetic algorithm
        """
        pass

    def gen_rand_individual(self):
        """Generate a random individual
        Returns:
            individual: a new individual
        """
        return [random.random() for _ in range(self.nb_genes)]

    def gen_init_population(self):
        """Generate some individuals for the first population
        It is used to add bootstrap individual
        Returns:
            individuals: list of individuals
        """
        return []

    def crossover(self, indiv_1, indiv_2, prob_1, prob_2):
        """Execute the crossover operation
        Default: implement the Parameterized Uniform Crossover
        See also: https://doi.org/10.21236/ADA293985
        Args:
            indiv_1 (list): firt individual
            indiv_2 (list): second individual
            prob_1 (float): value in [0, 1] is the probability of
                            an indiv_1 gene being chosen for the offspring
            prob_2 (float): value in [0, 1] is the probability of
                            an indiv_2 gene being chosen for the offspring
        Returns:
            offspring: list of offspring
        """
        if prob_1 < prob_2:
            indiv_1, indiv_2 = indiv_2, indiv_1
            prob_1, prob_2 = prob_2, prob_1

        offspring_1 = indiv_1[:self.nb_genes]

        for g in range(self.nb_genes):
            if random.random() < prob_1:
                offspring_1[g] = indiv_2[g]

        return [offspring_1]

    def stopping_criteria(self, population):
        """Verify whether the GA should stop or not
        Args:
            population (list): population of the current generation
        Returns:
            stop: a boolean value, True if algorithm should stop
        """
        return False

    def fitness(self, individual):
        """Calculate the fitness of an individual
        Args:
            indiv (list): indivual
        Returns:
            fitness: fitness value
        """
        return 0.0
