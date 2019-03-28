import csv
import random
import numpy as np
import sys
import time
# from pathos.threading import ThreadPool
from pathos.multiprocessing import ProcessPool
from util import input
from algo.util.metric import Metric
import algo


def exp_1(args=[]):
    random.seed()
    np.random.seed()

    pool = ProcessPool(4)

    r_nodes = [27]
    r_apps = range(10, 51, 10)
    r_users = range(1000, 10001, 3000)
    nb_runs = 30

    objectives = [("max_e", "get_qos_violation"),
                  ("avg_rt", "get_avg_response_time"),
                  ("cost", "get_cost"),
                  ("max_failure", "get_max_failure")]

    metrics = [("max_e", "get_qos_violation"),
               ("avg_e", "get_avg_deadline_violation"),
               ("deadline_sr", "get_deadline_satisfaction"),
               ("avg_rt", "get_avg_response_time"),
               ("max_usage", "get_max_resource_usage"),
               ("avg_usage", "get_avg_resource_usage"),
               ("power", "get_power_comsumption"),
               ("cost", "get_cost"),
               ("avg_availa", "get_avg_availability"),
               ("max_failure", "get_max_failure")]

    def exec_metrics(solution, output):
        for m_title, m_name in metrics:
            m_func = getattr(solution.metric, m_name)
            value = m_func(*solution.get_vars())
            output[m_title] = value
        return output

    def exec_solver(kwds):
        solver = kwds["solver"]
        params = kwds["params"]
        title = kwds["title"]
        version = kwds["version"]

        start_time = time.time()
        solution = solver.solve(**params)
        elapsed_time = time.time() - start_time
        output = {"nodes": nb_nodes,
                  "apps": nb_apps,
                  "users": nb_users,
                  "run": run,
                  "solution": title,
                  "version": version,
                  "time": elapsed_time
                  }

        return exec_metrics(solution, output)

    def write_output(output):
        print("{} {} | nodes: {} | apps: {} | users: {} | run: {}".format(
               output["solution"], output["version"], output["nodes"],
               output["apps"], output["users"], output["run"]
        ))
        print("\t {:15} : {} s".format("time", output["time"]))

        for m_title, m_name in metrics:
            print("\t {:15} : {}".format(m_title, output[m_title]))
        print(" ")

        writer.writerow(output)

    with open("output/result_exp_1.csv", "w") as csv_file:
        field_names = ["nodes", "apps", "users", "run", "solution", "version", "time"]
        for m_title, m_func_name in metrics:
            field_names.append(m_title)

        writer = csv.DictWriter(csv_file, fieldnames=field_names)
        writer.writeheader()

        config = input.Input("input.json")

        for nb_nodes in r_nodes:
            for nb_apps in r_apps:
                for nb_users in r_users:
                    for run in range(nb_runs):
                        config.gen_rand_data(nb_nodes, nb_apps, nb_users)
                        metric = Metric(config)
                        solvers = []

                        solver = algo.cloud
                        s_params = {"input": config}
                        s_title = "cloud"
                        s_version = ""
                        row = {"solver": solver, "params": s_params, "title": s_title, "version": s_version}
                        solvers.append(row)

                        obj_func = [getattr(metric, obj[1]) for obj in objectives]
                        mo_versions = [("v1", algo.genetic_mo), ("v2", algo.genetic_mo_2)]
                        for s_version, solver in mo_versions:
                            s_params = {"input": config, "objectives": obj_func}
                            s_title = "genetic_mo"
                            row = {"solver": solver, "params": s_params, "title": s_title, "version": s_version}
                            solvers.append(row)

                        for obj_title, obj_func_name in objectives:
                            obj_func = getattr(metric, obj_func_name)
                            solver = algo.genetic
                            s_params = {"input": config, "objective": obj_func}
                            s_title = "genetic"
                            s_version = obj_title
                            row = {"solver": solver, "params": s_params, "title": s_title, "version": s_version}
                            solvers.append(row)

                        solutions = pool.uimap(exec_solver, solvers)
                        for solution in solutions:
                            write_output(solution)
                        print("---")


def exp_2(args=[]):
    random.seed(1)
    np.random.seed(1)

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
               ("avg availa", metric.get_avg_availability),
               ("max failure", metric.get_max_failure)]

    solutions = [("cloud", algo.cloud),
                 ("genetic", algo.genetic),
                 ("genetic mo", algo.genetic_mo),
                 ("genetic mo 2", algo.genetic_mo_2)]

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


if __name__ == '__main__':
    args = sys.argv[1:]
    experiment = args[0] if args else 'exp_2'
    if experiment in locals():
        exp_func = locals()[experiment]
        exp_func(args[1:])
