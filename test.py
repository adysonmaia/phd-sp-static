import random
import numpy as np
import sys
import time
from util import input
from algo.util.metric import Metric
import algo


def exp_3(args=[]):
    random.seed()
    np.random.seed()

    nb_nodes = 27
    nb_apps = 30
    nb_users = 10000
    nb_runs = 5
    if len(args) >= 3:
        nb_nodes, nb_apps, nb_users = map(lambda i: int(i), args)

    config = input.Input("input.json")

    r_elite_prob = [0.5, 0.7, 0.9]
    r_elite_prop = [0.1, 0.3, 0.5, 0.7, 0.9]

    for run in range(nb_runs):
        config.gen_rand_data(nb_nodes, nb_apps, nb_users)
        metric = Metric(config)
        for elite_proportion in r_elite_prop:
            for elite_probability in r_elite_prob:
                solution = algo.genetic.solve(config,
                                              elite_proportion=elite_proportion,
                                              elite_probability=elite_proportion)
                value = metric.get_qos_violation(*solution.get_vars())
                print(run, elite_proportion, elite_probability, value)


def exp_2(args=[]):
    random.seed(3)
    np.random.seed(3)

    nb_nodes = 27
    nb_apps = 10
    nb_users = 1000
    if len(args) >= 3:
        nb_nodes, nb_apps, nb_users = map(lambda i: int(i), args)

    config = input.Input("input.json")
    config.gen_rand_data(nb_nodes, nb_apps, nb_users)
    metric = Metric(config)

    metrics = [("max e", metric.get_qos_violation),
               ("avg e", metric.get_avg_deadline_violation),
               ("deadline sr", metric.get_deadline_satisfaction),
               ("avg rt", metric.get_avg_response_time),
               ("max usage", metric.get_max_resource_usage),
               ("avg usage", metric.get_avg_resource_usage),
               ("power", metric.get_power_comsumption),
               ("cost", metric.get_cost),
               ("avg avail", metric.get_avg_availability),
               ("max unavail", metric.get_max_unavailability),
               ("avg unavail", metric.get_avg_unavailability)]

    # solutions = [("cloud", algo.cloud),
    #              ("genetic", algo.genetic),
    #              ("genetic mo", algo.genetic_mo),
    #              ("genetic mo 2", algo.genetic_mo_2),
    #              ("cluster", algo.cluster)]

    solutions = [("cloud", algo.cloud),
                 # ("milp", algo.milp),
                 ("genetic", algo.genetic),
                 # ("cluster", algo.cluster),
                 # ("cluster 2", algo.cluster_2)
                 ]

    for title, solver in solutions:
        start_time = time.time()
        solution = solver.solve(config)
        elapsed_time = round(time.time() - start_time, 4)
        print(title)
        print("\t {:15} : {} s".format("time", elapsed_time))
        print("\t {:15} : {}".format("valid", solution.is_valid()))

        for m_title, m_func in metrics:
            value = m_func(*solution.get_vars())
            print("\t {:15} : {}".format(m_title, value))

        if title == "milp":
            print("\t {:15} : {}".format("relaxed e", solution.e_relaxed))


if __name__ == '__main__':
    args = sys.argv[1:]
    experiment = args[0] if args else 'exp_2'
    if experiment in locals():
        exp_func = locals()[experiment]
        exp_func(args[1:])
