from algo.util import ga_bootstrap
from algo.genetic import SP_Chromosome
from algo.util.output import Output


def solve(input, version=2):

    solver_versions = [
        ga_bootstrap.create_individual_cloud,
        ga_bootstrap.create_individual_avg_delay,
        ga_bootstrap.create_individual_cluster,
        ga_bootstrap.create_individual_user,
        ga_bootstrap.create_individual_capacity
    ]
    nb_versions = len(solver_versions)

    solver = None
    if version < nb_versions:
        solver = solver_versions[version]
    else:
        def mixer_criation(c):
            func_1_index = ((version - nb_versions) // nb_versions) % nb_versions
            func_1 = solver_versions[func_1_index]
            func_2_index = version % nb_versions
            func_2 = solver_versions[func_2_index]

            return ga_bootstrap.merge_individual(c, func_1, func_2)
        solver = mixer_criation

    chromossome = SP_Chromosome(input)

    individual = solver(chromossome)
    result = chromossome.decode(individual)

    return Output(input).set_solution(*result)
