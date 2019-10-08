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
    'elite': {
        'label': 'Elite Proportion',
        'limit': [0, 1]
    },
    'mutant': {
        'label': 'Mutant Proportion',
        'limit': [0, 1]
    },
}

Y_PARAM = X_PARAM

SOL_LABEL = {
    ('milp', ''): r'MILP',
    ('bootstrap', 'cloud'): r'Cloud',
    ('bootstrap', 'net_delay'): r'NetDelay',
    ('bootstrap', 'cluster'): r'Cluster',
    ('bootstrap', 'deadline'): r'DL',
    ('bootstrap', 'net_delay_deadline'): r'NetDelay+DL',
    ('bootstrap', 'cluster_deadline'): r'Cluster+DL',
    ('genetic', ''): r'GA',
    ('genetic', 'bootstrap'): r'GA+HI',
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


def format_field(value, field):
    value = round(float(value), 2)
    if field == 'elite':
        value = 100 * value
    elif field == 'mutant':
        value = 100 * value

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
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    filtered = filter_data(data, **data_filter)
    z = []
    z_min = 0.0
    z_max = 0.0
    for x_value in x:
        for y_value in y:
            xy_filter = {x_field: x_value, y_field: y_value}
            xy_data = filter_data(filtered, **xy_filter)
            z_value = INF
            if len(xy_data) > 0:
                values = list(map(lambda r: format_metric(r[metric], metric), xy_data))
                mean, error = calc_stats(values)
                z_value = mean
                print("x {:.1f} y {:.1f} z {:.4f}".format(x_value, y_value, z_value))
                if z_value > z_max:
                    z_max = z_value
            z.append(z_value)

    x_param = X_PARAM[x_field]
    y_param = Y_PARAM[y_field]
    z_param = Z_PARAM[metric]

    x_ticks = [format_field(i, x_field) for i in x]
    y_ticks = [format_field(i, y_field) for i in y]

    ax.set_xlabel(x_param['label'])
    ax.set_ylabel(y_param['label'])
    ax.set_zlabel(z_param['label'])
    # ax.set_xlim(x[0] + x_param['limit'][0], x[-1] + x_param['limit'][1])
    # ax.set_ylim(x[0] + y_param['limit'][0], y[-1] + y_param['limit'][1])
    ax.set_zlim(*z_param['limit'])
    ax.set_xticks(x_ticks)
    ax.set_yticks(y_ticks)
    # plt.grid(True)

    x, y = np.meshgrid(x_ticks, y_ticks)
    norm = mpl.colors.Normalize(vmin=z_min, vmax=z_max)
    # norm = mpl.colors.LogNorm(vmin=z_min, vmax=z_max)
    ax.scatter(x, y, z, c=z, cmap='seismic', norm=norm)
    if not filename:
        plt.show()
    else:
        plt.savefig(filename, dpi=DPI)


def run():
    data = get_data_from_file('exp/output/exp_3.csv')

    all_solutions = [
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
            'title': 'ga_em_params',
            'filter': {},
            'x_field': 'elite',
            'x_values': np.arange(0, 1.1, 0.2),
            'y_field': 'mutant',
            'y_values': np.arange(0, 1.1, 0.2)
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
