import csv
import random
import numpy as np
import sys
import time
from pathos.multiprocessing import ProcessPool
from util import input
from algo.util.metric import Metric
import algo


def exec_solver(solver_data):
    solver = solver_data.solver
    params = solver_data.params

    start_time = time.time()
    solution = solver.solve(**params)
    elapsed_time = time.time() - start_time

    solver_data.time = elapsed_time
    solver_data.solution = solution

    return solver_data


class Solver_Data():
    def __init__(self):
        pass


class Exp_1():
    def __init__(self):
        random.seed()
        np.random.seed()

        self.pool = ProcessPool(4)
        self.nb_runs = 30

        self.input_filename = "input.json"
        self.output_filename = "output/result_exp_1.csv"

        self.scenarios = [
            {"nodes": [27], "apps": range(10, 51, 10), "users": [10000]},
            {"nodes": [27], "apps": [50], "users": range(1000, 10001, 3000)},
        ]

        self.objectives = [("max_e", "get_qos_violation"),
                           ("cost", "get_cost"),
                           ("avg_unavail", "get_avg_unavailability")]

        self.metrics = [("max_e", "get_qos_violation"),
                        ("avg_e", "get_avg_deadline_violation"),
                        ("deadline_sr", "get_deadline_satisfaction"),
                        ("avg_rt", "get_avg_response_time"),
                        ("max_usage", "get_max_resource_usage"),
                        ("avg_usage", "get_avg_resource_usage"),
                        ("power", "get_power_comsumption"),
                        ("cost", "get_cost"),
                        ("avg_avail", "get_avg_availability"),
                        ("max_unavail", "get_max_unavailability"),
                        ("avg_unavail", "get_avg_unavailability")]

    def run(self):
        with open(self.output_filename, "w") as csv_file:
            field_names = ["nodes", "apps", "users", "run", "solution", "version", "time"]
            for m_title, m_func_name in self.metrics:
                field_names.append(m_title)

            self.writer = csv.DictWriter(csv_file, fieldnames=field_names)
            self.writer.writeheader()

            for scenario in self.scenarios:
                self._run_scenario(scenario)

    def _run_scenario(self, scenario):
        r_runs = range(self.nb_runs)
        r_nodes = scenario["nodes"]
        r_apps = scenario["apps"]
        r_users = scenario["users"]

        for nb_nodes in r_nodes:
            for nb_apps in r_apps:
                for nb_users in r_users:
                    solvers = []
                    for run in r_runs:
                        solvers += self._get_solvers(nb_nodes, nb_apps, nb_users, run)

                    solutions = self.pool.uimap(exec_solver, solvers)
                    for data in solutions:
                        output = self._get_output(data)
                        self._write_output(output)

    def _get_solvers(self, nb_nodes, nb_apps, nb_users, run):
        config = input.Input(self.input_filename)
        config.gen_rand_data(nb_nodes, nb_apps, nb_users)
        metric = Metric(config)
        solvers = []

        data = Solver_Data()
        data.solver = algo.cloud
        data.params = {"input": config}
        data.title = "cloud"
        data.version = ""
        data.nb_nodes = nb_nodes
        data.nb_apps = nb_apps
        data.nb_users = nb_users
        data.run = run
        solvers.append(data)

        obj_func = [getattr(metric, obj[1]) for obj in self.objectives]
        mo_versions = [("v1", algo.genetic_mo), ("v2", algo.genetic_mo_2)]
        for s_version, solver in mo_versions:
            data = Solver_Data()
            data.solver = solver
            data.params = {"input": config, "objectives": obj_func}
            data.title = "genetic_mo"
            data.version = s_version
            data.nb_nodes = nb_nodes
            data.nb_apps = nb_apps
            data.nb_users = nb_users
            data.run = run
            solvers.append(data)

        for obj_title, obj_func_name in self.objectives:
            obj_func = getattr(metric, obj_func_name)
            data = Solver_Data()
            data.solver = algo.genetic
            data.params = {"input": config, "objective": obj_func}
            data.title = "genetic"
            data.version = obj_title
            data.nb_nodes = nb_nodes
            data.nb_apps = nb_apps
            data.nb_users = nb_users
            data.run = run
            solvers.append(data)

        return solvers

    def _get_output(self, data):
        output = {
            "nodes": data.nb_nodes,
            "apps": data.nb_apps,
            "users": data.nb_users,
            "run": data.run,
            "solution": data.title,
            "version": data.version,
            "time": data.time
        }

        for m_title, m_name in self.metrics:
            solution = data.solution
            m_func = getattr(solution.metric, m_name)
            value = m_func(*solution.get_vars())
            output[m_title] = value

        return output

    def _write_output(self, output):
        print("{} {} | nodes: {} | apps: {} | users: {} | run: {}".format(
               output["solution"], output["version"], output["nodes"],
               output["apps"], output["users"], output["run"]
        ))
        print("\t {:15} : {} s".format("time", output["time"]))

        for m_title, m_name in self.metrics:
            print("\t {:15} : {}".format(m_title, output[m_title]))
        print(" ")

        self.writer.writerow(output)


def exp_1(args=[]):
    exp = Exp_1()
    exp.run()


if __name__ == '__main__':
    args = sys.argv[1:]
    experiment = args[0] if args else 'exp_1'
    if experiment in locals():
        exp_func = locals()[experiment]
        exp_func(args[1:])
