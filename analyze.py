import csv
import numpy as np
import scipy.stats as st
import matplotlib.pyplot as plt

DPI = 100
Y_LIMITS = [-0.2, 11]
Y_TICKS = range(0, 13, 1)
Y_LABEL = "QoS Violation (e) - ms"


def get_data_from_file(filename):
    results = []
    with open(filename) as csv_file:
        csv_reader = csv.DictReader(csv_file)
        line_count = 0
        for row in csv_reader:
            if line_count > 0:
                results.append(row)
            line_count += 1
    return results


def filter_data(data, apps=[], nodes=[], users=[], solutions=[]):
    return filter(lambda row: ((not apps or int(row["apps"]) in apps)
                               and (not nodes or int(row["nodes"]) in nodes)
                               and (not users or int(row["users"]) in users)
                               and (not solutions or row["solution"] in solutions)),
                  data)


def gen_apps_figure(data, solutions, apps, nb_nodes, nb_users,
                    filename=None, nb_runs=30):
    plt.clf()
    filtered = filter_data(data, nodes=[nb_nodes], users=[nb_users])
    formats = ["-o", "-^"]
    formats_len = len(formats)
    line = 0
    x = apps
    for solution in solutions:
        sol_data = filter_data(filtered, solutions=[solution])
        y = []
        y_errors = []
        for nb_apps in apps:
            data = filter_data(sol_data, apps=[nb_apps])
            values = map(lambda row: float(row["value"]), data)
            mean = np.mean(values)
            error = st.t.interval(0.95, nb_runs - 1, loc=mean, scale=st.sem(values))
            y.append(mean)
            y_errors.append(error[1] - mean)

        line_format = formats[line % formats_len]
        plt.errorbar(x, y, yerr=y_errors, label=solution, fmt=line_format)
        line += 1

    plt.legend(loc='upper left', numpoints=1)
    plt.xlabel('Number of Applications')
    plt.ylabel(Y_LABEL)
    plt.xlim(x[0]-1, x[-1]+1)
    plt.xticks(x)
    plt.ylim(*Y_LIMITS)
    plt.yticks(Y_TICKS)
    plt.grid(True)
    if not filename:
        plt.show()
    else:
        plt.savefig(filename, dpi=DPI)


def gen_users_figure(data, solutions, users, nb_apps, nb_nodes,
                     filename=None, nb_runs=30):
    plt.clf()
    filtered = filter_data(data, apps=[nb_apps], nodes=[nb_nodes])
    formats = ["-o", "-^"]
    formats_len = len(formats)
    line = 0
    x = users
    for solution in solutions:
        sol_data = filter_data(filtered, solutions=[solution])
        y = []
        y_errors = []
        for nb_users in users:
            data = filter_data(sol_data, users=[nb_users])
            values = map(lambda row: float(row["value"]), data)
            mean = np.mean(values)
            error = st.t.interval(0.95, nb_runs - 1, loc=mean, scale=st.sem(values))
            y.append(mean)
            y_errors.append(error[1] - mean)

        line_format = formats[line % formats_len]
        plt.errorbar(x, y, yerr=y_errors, label=solution, fmt=line_format)
        line += 1

    plt.legend(loc='upper left', numpoints=1)
    plt.xlabel('Number of Users')
    plt.ylabel(Y_LABEL)
    plt.xlim(x[0]-100, x[-1]+100)
    plt.xticks(x)
    plt.ylim(*Y_LIMITS)
    plt.yticks(Y_TICKS)
    plt.grid(True)
    if not filename:
        plt.show()
    else:
        plt.savefig(filename, dpi=DPI)


def gen_users_apps_figure(data, solutions, users, apps, nb_nodes,
                          filename=None, nb_runs=30):
    plt.clf()
    filtered = filter_data(data, nodes=[nb_nodes])
    formats = ["-o", "-^", "-s", "--o", "--^", "--s"]
    formats_len = len(formats)
    line = 0
    x = users
    for solution in solutions:
        for nb_apps in apps:
            sol_data = filter_data(filtered, solutions=[solution], apps=[nb_apps])
            y = []
            y_errors = []
            for nb_users in users:
                data = filter_data(sol_data, users=[nb_users])
                values = map(lambda row: float(row["value"]), data)
                mean = np.mean(values)
                sem = st.sem(values)  # Std Error Mean
                if mean > 0.0 and sem > 0.0:
                    error = st.t.interval(0.95, nb_runs - 1, loc=mean, scale=sem)
                else:
                    error = [0.0, 0.0]
                y.append(mean)
                y_errors.append(error[1] - mean)

            line_format = formats[line % formats_len]
            line_label = "%s (%d apps)" % (solution, nb_apps)
            plt.errorbar(x, y, yerr=y_errors, label=line_label, fmt=line_format)
            line += 1

    plt.legend(loc='upper left', ncol=2, numpoints=1)
    plt.xlabel('Number of Users')
    plt.ylabel(Y_LABEL)
    plt.xlim(x[0]-100, x[-1]+100)
    plt.xticks(x)
    plt.ylim(Y_LIMITS[0], 13)
    plt.yticks(Y_TICKS)
    plt.grid(True)
    if not filename:
        plt.show()
    else:
        plt.savefig(filename, dpi=DPI)


def main():
    data = get_data_from_file("output/result.csv")
    solutions = ["greedy", "genetic"]

    # users = range(1000, 10001, 3000)
    # # gen_users_figure(data, solutions, users, 30, 9, filename="output/fig_users.png")
    # gen_users_figure(data, solutions, users, 30, 9)

    apps = range(10, 51, 10)
    gen_apps_figure(data, solutions, apps, nb_nodes=9, nb_users=4000)

    # users = range(1000, 10001, 3000)
    # apps = [10, 30, 50]
    # gen_users_apps_figure(data, solutions, users, apps, nb_nodes=9)


if __name__ == '__main__':
    main()
