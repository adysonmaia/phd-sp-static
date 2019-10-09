from algo.util import ga_heuristic
from algo.genetic import SP_Chromosome
from algo.util.output import Output


def solve(input, version=None, objective=None):
    solver_versions = {
        "cloud": ga_heuristic.create_individual_cloud,
        "net_delay": ga_heuristic.create_individual_net_delay,
        "cluster_metoids": ga_heuristic.create_individual_cluster_metoids,
        "deadline": ga_heuristic.create_individual_deadline,
        "cluster_metoids_sc": ga_heuristic.create_individual_cluster_metoids_sc
    }

    if version is None:
        version = ["net_delay", "deadline"]

    functions = []
    if isinstance(version, list) or isinstance(version, tuple):
        functions = [solver_versions[v] for v in version]
    else:
        functions = [solver_versions[version]]

    chromosome = SP_Chromosome(input, objective=objective)
    individual = ga_heuristic.merge_creation_functions(chromosome, functions)
    result = chromosome.decode(individual)

    return Output(input).set_solution(*result)
