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


class Exp_3():
    def __init__(self):
        random.seed()
        np.random.seed()

        self.pool = ProcessPool(EXP_POOL_SIZE)
        self.nb_runs = 30
        self.nb_nodes = 27
        self.nb_apps = 50
        self.nb_users = 10000

        self.input_filename = "exp/input/exp_3.json"
        self.output_filename = "exp/output/exp_3.csv"

        self.scenarios = []
        for e in np.arange(0, 1.1, 0.1):
            for m in np.arange(0, 1.1, 0.1):
                if e + m > 1:
                    continue
                param = {'elite': e, 'mutant': m}
                self.scenarios.append(param)

        self.objective = ("max_dv", "get_max_deadline_violation")

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
                "elite", "mutant", "run", "solution", "version",
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
                nb_elites = scenario['elite']
                nb_mutants = scenario['mutant']
                solvers += self._get_solvers(nb_elites, nb_mutants,
                                             run, input, metric)

            solutions = self.pool.uimap(exec_solver, solvers)
            for data in solutions:
                output = self._get_output(data)
                self._write_output(output)

    def _get_solvers(self, nb_elites, nb_mutants, run, input, metric):
        obj_title, obj_func_name = self.objective
        obj_func = getattr(metric, obj_func_name)

        solvers = []

        data = Solver_Data()
        data.solver = algo.genetic
        data.params = {
            "input": input,
            "objective": obj_func,
            "use_bootstrap": True,
            "pool_size": GA_POOL_SIZE,
            "elite_proportion": nb_elites,
            "mutant_proportion": nb_mutants
        }
        data.title = "genetic"
        data.version = "bootstrap"
        data.objective = obj_title
        data.elite = nb_elites
        data.mutant = nb_mutants
        data.run = run
        solvers.append(data)

        return solvers

    def _get_output(self, data):
        output = {
            "elite": data.elite,
            "mutant": data.mutant,
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
        print("{} {} | elite: {} | mutant: {} | run: {}".format(
               output["solution"], output["version"], output["elite"],
               output["mutant"], output["run"]
        ))
        print("\t {:15} : {} s".format("time", output["time"]))
        print("\t {:15} : {}".format("objective", output["objective"]))

        for m_title, m_name in self.metrics:
            print("\t {:15} : {}".format(m_title, output[m_title]))
        print(" ")

        self.writer.writerow(output)


def run():
    exp = Exp_3()
    exp.run()


if __name__ == '__main__':
    print("Execute as 'python3 main.py exp_3'")
