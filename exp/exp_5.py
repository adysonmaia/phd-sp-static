import csv
import random
import numpy as np
import time
from pathos.multiprocessing import ProcessPool
from util import generator
from algo.util.metric import Metric
import algo

EXP_POOL_SIZE = 3
GA_POOL_SIZE = 4


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


class Exp_5():
    def __init__(self):
        random.seed()
        np.random.seed()

        self.pool = ProcessPool(EXP_POOL_SIZE)
        self.nb_runs = 30
        self.nb_nodes = 27
        self.nb_apps = 50
        self.nb_users = 10000

        self.input_filename = "exp/input/exp_5.json"
        self.output_filename = "exp/output/exp_5.csv"

        self.scenarios = []
        for i in np.arange(0.0, 0.6, 0.1):
            param = {'stop_threshold': i}
            self.scenarios.append(param)

        self.multi_objective = [
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
            ("avg_unavail", "get_avg_unavailability")
        ]

        self.app_types = ["eMBB", "URLLC", "mMTC"]

    def run(self):
        with open(self.output_filename, "w") as csv_file:
            field_names = [
                "threshold", "run", "solution", "version",
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

            self._run_scenarios()

    def _run_scenarios(self):
        r_runs = range(self.nb_runs)

        for run in r_runs:
            solvers = []
            input = generator.InputGenerator().gen_from_file(
                self.input_filename, self.nb_nodes, self.nb_apps, self.nb_users
            )
            metric = Metric(input)

            for scenario in self.scenarios:
                st = scenario['stop_threshold']
                solvers += self._get_solvers(st, run, input, metric)

            solutions = self.pool.uimap(exec_solver, solvers)
            for data in solutions:
                output = self._get_output(data)
                self._write_output(output)

    def _get_solvers(self, stop_threshold, run, input, metric):
        solvers = []

        mo_func = [getattr(metric, obj[1]) for obj in self.multi_objective]
        mo_title = [obj[0] for obj in self.multi_objective]
        data = Solver_Data()
        data.solver = algo.genetic_mo
        data.params = {
            "input": input,
            "objective": mo_func,
            "use_heuristic": True,
            "pool_size": GA_POOL_SIZE,
            "stop_threshold": stop_threshold
        }
        data.title = "moga"
        data.version = "preferred"
        data.objective = "|".join(mo_title)
        data.stop_threshold = stop_threshold
        data.run = run
        solvers.append(data)

        return solvers

    def _get_output(self, data):
        output = {
            "stop_threshold": data.stop_threshold,
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
        print("{} {} | stop threshold : {} | run: {}".format(
               output["solution"], output["version"],
               output["stop_threshold"], output["run"]
        ))
        print("\t {:15} : {} s".format("time", output["time"]))
        print("\t {:15} : {}".format("objective", output["objective"]))

        for m_title, m_name in self.metrics:
            print("\t {:15} : {}".format(m_title, output[m_title]))
        print(" ")

        self.writer.writerow(output)


def run():
    exp = Exp_5()
    exp.run()


if __name__ == '__main__':
    print("Execute as 'python3 main.py exp_5'")
