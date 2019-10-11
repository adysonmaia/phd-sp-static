import csv
import numpy as np
import scipy.stats as st
import matplotlib as mpl
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D


DPI = 100
INF = float("inf")
# INF = 1000

LINE_FORMATS = [
    {'fmt': '-^'},
    {'fmt': '-v'},
    {'fmt': '-<'},
    {'fmt': '-d', 'fillstyle': 'none'},
    {'fmt': '-d'},
    {'fmt': '-s', 'fillstyle': 'none'},
    {'fmt': '-s'},
    {'fmt': '-o', 'fillstyle': 'none'},
    {'fmt': '-o'},
]

Z_PARAM = {
    'max_dv': {
        'label': 'Deadline Violation - ms',
        'limit': [0.0, 13.0],
        'labelpad': 10
    },
    'dsr': {
        'label': 'Deadline Satisfaction - %',
        'limit': [40.0, 100.0],
        'labelpad': 10
    },
    'avg_rt': {
        'label': 'Response Time - ms',
        'limit': [0.0, 18.0],
        'labelpad': 10
    },
    'cost': {
        'label': 'Cost',
        'limit': [1200.0, 1600.0],
        'labelpad': 20
    },
    'max_unavail': {
        'label': 'Availability - %',
        'limit': [90.0, 100.0],
        'labelpad': 15
    },
    # 'avg_unavail': {
    #     'label': 'Availability - %',
    #     'limit': [90.0, 100.0],
    #     'labelpad': 15
    # },
    'avg_unavail': {
        'label': 'Unavailability - %',
        'limit': [0.0, 10.0],
        'labelpad': 15
    },
    'avg_avail': {
        'label': 'Availability - %',
        'limit': [90.0, 100.0],
        'labelpad': 15
    }
}

X_PARAM = {
    'elite': {
        'label': 'Elite - %',
        'limit': [0, 100]
    },
    'mutant': {
        'label': 'Mutant - %',
        'limit': [0, 100]
    },
}

Y_PARAM = X_PARAM

SOL_LABEL = {
    ('milp', ''): r'MILP',
    ('heuristic', 'cloud'): r'Cloud',
    ('heuristic', 'net_delay'): r'NetDelay',
    ('heuristic', 'cluster'): r'Cluster',
    ('heuristic', 'deadline'): r'DL',
    ('heuristic', 'net_delay_deadline'): r'NetDelay+DL',
    ('heuristic', 'cluster_deadline'): r'Cluster+DL',
    ('soga', ''): r'GA',
    ('soga', 'heuristic'): r'GA+HI',
    ('moga', 'preferred'): r'GA',
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
        # value = 100.0 * (1.0 - value)
        value = 100.0 * value
    elif metric == 'avg_avail':
        value = 100.0 * value
    elif metric == 'dsr':
        value = 100.0 * value

    return value


def format_field(value, field):
    value = float(value)
    if field == 'elite' or field == 'mutant':
        value = round(100 * value)

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


def gen_figure(data, metric, x, x_field, y, y_field,
               data_filter, filename=None):
    plt.clf()
    mpl.rcParams.update({'font.size': 20})
    ax = plt.axes(projection='3d')

    filtered = filter_data(data, **data_filter)
    dim = (len(x), len(y))
    x_2d = np.zeros(dim)
    y_2d = np.zeros(dim)
    z_2d = np.zeros(dim)
    for x_index, x_value in enumerate(x):
        for y_index, y_value in enumerate(y):
            xy_filter = {x_field: x_value, y_field: y_value}
            xy_data = filter_data(filtered, **xy_filter)
            z_value = INF
            if len(xy_data) > 0:
                values = list(map(lambda r: format_metric(r[metric], metric), xy_data))
                mean, error = calc_stats(values)
                z_value = mean
                print("{} x={:.1f}, y={:.1f}, z={:.4f}".format(metric, x_value, y_value, z_value))

            x_2d[x_index][y_index] = format_field(x_value, x_field)
            y_2d[x_index][y_index] = format_field(y_value, y_field)
            z_2d[x_index][y_index] = z_value

    x_param = X_PARAM[x_field]
    y_param = Y_PARAM[y_field]
    z_param = Z_PARAM[metric]

    z_min, z_max = z_param['limit']

    ax.set_xlabel(x_param['label'], labelpad=20)
    ax.set_ylabel(y_param['label'], labelpad=20)
    # ax.set_zlabel(z_param['label'], labelpad=z_param['labelpad'])
    # ax.set_xlim(*x_param['limit'])
    # ax.set_ylim(*y_param['limit'])
    ax.set_zlim(z_min, z_max)
    # ax.set_xticks(x_ticks)
    # ax.set_yticks(y_ticks)

    # color_map = 'seismic'
    color_map = 'plasma'
    # color_map = 'inferno'
    # color_map = 'magma'
    # color_map = 'viridis'

    plt.subplots_adjust(bottom=0.1, top=1.0, left=-0.10, right=0.92)
    surf = ax.plot_surface(x_2d, y_2d, z_2d, cmap=color_map, vmin=z_min, vmax=z_max)
    cb = plt.colorbar(surf, shrink=0.5)
    cb.set_label(z_param['label'])

    # plt.show()
    if not filename:
        plt.show()
    else:
        plt.savefig(filename, dpi=DPI)


def run():
    data = get_data_from_file('exp/output/exp_3.csv')

    all_solutions = [
        # ('soga', 'heuristic'),
        ('moga', 'preferred'),
    ]

    metric_solutions = {
        'max_dv': all_solutions,
        # 'dsr': all_solutions,
        # 'avg_rt': all_solutions,
        'cost': all_solutions,
        'avg_unavail': all_solutions
    }

    params = [
        {
            'title': 'em',
            'filter': {},
            'x_field': 'elite',
            # 'x_values': np.arange(0, 1.1, 0.1),
            'x_values': np.arange(0, 0.6, 0.1),
            'y_field': 'mutant',
            # 'y_values': np.arange(0, 1.1, 0.1)
            'y_values': np.arange(0, 0.6, 0.1)
        },
    ]

    for param in params:
        for metric, solutions in metric_solutions.items():
            for solution, sol_version in solutions:
                fig_title = param['title']
                filter = param['filter']
                filter['solution'] = solution
                filter['version'] = sol_version
                x = param['x_values']
                x_field = param['x_field']
                y = param['y_values']
                y_field = param['y_field']
                filename = "exp/figs/exp_3/fig_{}_{}_{}_{}.png".format(
                    fig_title, metric, solution, sol_version
                )
                gen_figure(data, metric, x, x_field, y, y_field,
                           filter, filename)


if __name__ == '__main__':
    print("Execute as 'python3 analyze.py exp_1'")
