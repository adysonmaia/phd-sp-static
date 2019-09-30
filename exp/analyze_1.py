import csv
import numpy as np
import scipy.stats as st
import matplotlib
import matplotlib.pyplot as plt


DPI = 100

LINE_FORMATS = [
    '-o',   '-s',  '-D',  '-^',  '-v',  '-<', '->',
    # '--o', '--s', '--D', '--^', '--v', '--<', '-->',
    # '-.o', '-.s', '-.D', '-.^', '-.v', '-.<', '-.>',
]

Y_PARAM = {
    'max_dv': {
        'label': 'Deadline Violation - ms',
        'limit': [0.0, 14.0]
    },
    'dsr': {
        'label': 'Deadline Satisfaction - %',
        'limit': [40.0, 100.0]
    },
    'avg_rt': {
        'label': 'Response Time - ms',
        'limit': [0.0, 18.0]
    },
    'cost': {
        'label': 'Cost',
        'limit': [0.0, 2500.0]
    },
    'max_unavail': {
        'label': 'Availability - %',
        'limit': [70.0, 100.0]
    },
    'avg_unavail': {
        'label': 'Availability - %',
        'limit': [70.0, 100.0]
    },
    'avg_avail': {
        'label': 'Availability - %',
        'limit': [0.0, 100.0]
    }
}

X_PARAM = {
    'users': {
        'label': 'Number of Users',
        'limit': [-100, 100]
    },
    'apps': {
        'label': 'Number of Applications',
        'limit': [-0.5, 0.5]
    },
    'nodes': {
        'label': 'Number of Nodes',
        'limit': [-0.2, 0.2]
    }
}

SOL_LABEL = {
    ('milp', ''): r'MILP',
    ('bootstrap', 'cloud'): r'Cloud',
    ('bootstrap', 'net_delay'): r'Net Delay',
    ('bootstrap', 'cluster'): r'Cluster',
    ('bootstrap', 'deadline'): r'Deadline',
    ('bootstrap', 'net_delay_deadline'): r'Net Delay + Deadline',
    ('bootstrap', 'cluster_deadline'): r'Cluster + Deadline',
    ('genetic', ''): r'Genetic',
    ('genetic', 'bootstrap'): r'Genetic + Bootstrap',
}


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


def filter_data(data, **kwargs):
    def to_string_values(values):
        str_values = []
        if not isinstance(values, list):
            values = [values]
        for value in values:
            str_values.append(str(value))
        return str_values

    def in_filter(row):
        for key, value in row.items():
            if key in f_values and value not in f_values[key]:
                return False
        return True

    f_values = {k: to_string_values(v) for k, v in kwargs.items()}
    return list(filter(lambda row: in_filter(row), data))


def format_metric(value, metric):
    value = float(value)
    if metric == 'max_unavail':
        value = 100.0 * (1.0 - value)
    elif metric == 'avg_unavail':
        value = 100.0 * (1.0 - value)
    elif metric == 'avg_avail':
        value = 100.0 * value
    elif metric == 'dsr':
        value = 100.0 * value

    return value


def calc_stats(values):
    nb_runs = len(values)
    mean = np.mean(values)
    sem = st.sem(values)
    if sem > 0.0:
        # Calc confidence interval, return [mean - e, mean + e]
        error = st.t.interval(0.95, nb_runs - 1, loc=mean, scale=sem)
        error = error[1] - mean
    else:
        error = 0.0
    return mean, error


def gen_figure(data, solutions, metric, x, x_field, data_filter, filename=None):
    plt.clf()
    matplotlib.rcParams.update({'font.size': 20})
    filtered = filter_data(data, **data_filter)
    # formats = ['-o', '-s', '-<', 'k-->', '-^', '-v', '-d']
    # formats = ['-', '--', '-.', ':']
    formats = LINE_FORMATS
    formats_len = len(formats)
    line = 0
    for solution, version in solutions:
        sol_data = filter_data(filtered, solution=solution, version=version)
        y = []
        y_errors = []
        for i in x:
            x_filter = {x_field: i}
            x_data = filter_data(sol_data, **x_filter)
            values = list(map(lambda r: format_metric(r[metric], metric), x_data))
            mean, error = calc_stats(values)
            y.append(mean)
            y_errors.append(error)

        line_format = formats[line % formats_len]
        label = SOL_LABEL[solution, version]
        plt.errorbar(x, y, yerr=y_errors, label=label,
                     fmt=line_format, markersize=10)
        line += 1

    # ncol = 4 if len(solutions) > 4 else 3
    ncol = 4
    plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.17),
               numpoints=1, ncol=ncol, columnspacing=0.5, fontsize=20)
    plt.subplots_adjust(bottom=0.2, top=0.97, left=0.12, right=0.96)

    x_param = X_PARAM[x_field]
    y_param = Y_PARAM[metric]

    plt.xlabel(x_param['label'])
    plt.ylabel(y_param['label'])
    plt.xlim(x[0] + x_param['limit'][0], x[-1] + x_param['limit'][1])
    plt.ylim(*y_param['limit'])
    plt.xticks(x)
    plt.grid(True)
    if not filename:
        plt.show()
    else:
        plt.savefig(filename, dpi=DPI, bbox_inches='tight', pad_inches=0.05)


def run():
    data = get_data_from_file('exp/output/exp_1.csv')

    all_solutions = [
        ('bootstrap', 'cloud'),
        ('milp', ''),
        ('bootstrap', 'net_delay'),
        ('bootstrap', 'net_delay_deadline'),
        ('bootstrap', 'cluster'),
        ('bootstrap', 'cluster_deadline'),
        ('genetic', ''),
        ('genetic', 'bootstrap'),
    ]

    metric_solutions = {
        'max_dv': all_solutions,
        # 'dsr': all_solutions,
        # 'avg_rt': all_solutions,
        # 'cost': all_solutions,
        # 'avg_unavail': all_solutions
    }

    params = [
        {
            'title': 'a_50_n_27',
            'filter': {'apps': 50, 'nodes': 27},
            'x_field': 'users',
            'x_values': [1000, 4000, 7000, 10000]
        },
        {
            'title': 'u_10k_n_27',
            'filter': {'users': 10000, 'nodes': 27},
            'x_field': 'apps',
            'x_values': [10, 20, 30, 40, 50]
        },
        {
            'title': 'a_50_u_10k',
            'filter': {'apps': 50, 'users': 10000},
            'x_field': 'nodes',
            'x_values': [6, 11, 18, 27]
        }
    ]

    for param in params:
        for metric, solutions in metric_solutions.items():
            fig_title = param['title']
            filter = param['filter']
            x = param['x_values']
            x_field = param['x_field']
            filename = "exp/figs/exp_1/fig_{}_{}.png".format(metric, fig_title)
            gen_figure(data, solutions, metric, x, x_field, filter, filename)


if __name__ == '__main__':
    print("Execute as 'python3 analyze.py exp_1'")
