import csv
import random
import numpy as np
import time
from pathos.multiprocessing import ProcessPool
from util import generator
from algo.util.metric import Metric
import algo

EXP_POOL_SIZE = 5
GA_POOL_SIZE = 3


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


class Exp_2():
    def __init__(self):
        random.seed()
        np.random.seed()

        self.pool = ProcessPool(EXP_POOL_SIZE)
        self.nb_runs = 30

        self.input_filename = "exp/input/exp_2.json"
        self.output_filename = "exp/output/exp_2.csv"

        self.scenarios = [
            {"nodes": [27], "apps": [10, 20, 30, 40], "users": [10000]},
            {"nodes": [27], "apps": [50], "users": [1000, 4000, 7000, 10000]},
            {"nodes": [6, 11, 18], "apps": [50], "users": [10000]},
        ]

        self.objectives = [
            ("max_dv", "get_max_deadline_violation"),
            ("cost", "get_overall_cost"),
            ("avg_unavail", "get_avg_unavailability"),
            # ("avg_rt", "get_avg_response_time"),
            # ("power", "get_overall_power_comsumption"),
        ]

        self.metrics = [
            ("max_dv", "get_max_deadline_violation"),
            ("avg_dv", "get_avg_deadline_violation"),
            ("dsr", "get_deadline_satisfaction"),
            ("avg_rt", "get_avg_response_time"),
            ("cost", "get_overall_cost"),
            ("avg_unavail", "get_avg_unavailability"),
            # ("power", "get_overall_power_comsumption"),
        ]

        self.app_types = ["eMBB", "URLLC", "mMTC"]

    def run(self):
        with open(self.output_filename, "w") as csv_file:
            field_names = [
                "nodes", "apps", "users", "run", "solution", "version",
                "time", "objective"
            ]
            for m_title, m_func_name in self.metrics:
                field_names.append(m_title)
            for type in self.app_types:
                for m_title, m_func_name in self.metrics:
                    m_title = type + "_" + m_title
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
                        solvers += self._get_solvers(nb_nodes, nb_apps,
                                                     nb_users, run)

                    solutions = self.pool.uimap(exec_solver, solvers)
                    for data in solutions:
                        output = self._get_output(data)
                        self._write_output(output)

    def _get_solvers(self, nb_nodes, nb_apps, nb_users, run):
        input = generator.InputGenerator().gen_from_file(
            self.input_filename, nb_nodes, nb_apps, nb_users
        )
        metric = Metric(input)
        solvers = []

        for obj_title, obj_func_name in self.objectives:
            obj_func = getattr(metric, obj_func_name)
            for use_heuristic in [True, False]:
                data = Solver_Data()
                data.solver = algo.genetic_mo
                data.params = {
                    "input": input,
                    "objective": [obj_func],
                    "use_heuristic": use_heuristic,
                    "pool_size": GA_POOL_SIZE
                }
                data.title = "soga" + ("_hi" if use_heuristic else "")
                data.version = obj_title
                data.objective = obj_title
                data.nb_nodes = nb_nodes
                data.nb_apps = nb_apps
                data.nb_users = nb_users
                data.run = run
                solvers.append(data)

        obj_func = [getattr(metric, obj[1]) for obj in self.objectives]
        obj_title = [obj[0] for obj in self.objectives]
        mo_versions = [("preferred", algo.genetic_mo),
                       ("pareto", algo.genetic_mo_pareto)]
        for s_version, solver in mo_versions:
            for use_heuristic in [True, False]:
                data = Solver_Data()
                data.solver = solver
                data.params = {
                    "input": input,
                    "objective": obj_func,
                    "use_heuristic": use_heuristic,
                    "pool_size": GA_POOL_SIZE
                }
                data.title = "moga" + ("_hi" if use_heuristic else "")
                data.version = s_version
                data.objective = "|".join(obj_title)
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
            "time": data.time,
            "objective": data.objective,
        }

        for m_title, m_func_name in self.metrics:
            solution = data.solution
            m_func = getattr(solution.metric, m_func_name)
            value = m_func(*solution.get_vars())
            output[m_title] = value

        for type in self.app_types:
            solution.metric.filter.clean()
            solution.metric.filter.set_app_type(type)
            for m_title, m_func_name in self.metrics:
                m_title = type + "_" + m_title
                m_func = getattr(solution.metric, m_func_name)
                value = m_func(*solution.get_vars())
                output[m_title] = value

        return output

    def _write_output(self, output):
        print("{} {} | nodes: {} | apps: {} | users: {} | run: {}".format(
               output["solution"], output["version"], output["nodes"],
               output["apps"], output["users"], output["run"]
        ))
        print("\t {:15} : {} s".format("time", output["time"]))
        print("\t {:15} : {}".format("objective", output["objective"]))

        for m_title, m_name in self.metrics:
            print("\t {:15} : {}".format(m_title, output[m_title]))
        print(" ")

        self.writer.writerow(output)


def run():
    exp = Exp_2()
    exp.run()


if __name__ == '__main__':
    print("Execute as 'python3 main.py exp_2'")
