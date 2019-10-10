import csv
import numpy as np
import scipy.stats as st
import matplotlib
import matplotlib.pyplot as plt


DPI = 100

Y_PARAM = {
    'max_dv': {
        'label': 'Deadline Violation - ms',
        'limit': [0.0, 8.0]
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
        'limit': [1000.0, 1500.0]
    },
    'max_unavail': {
        'label': 'Availability - %',
        'limit': [70.0, 100.0]
    },
    'avg_unavail': {
        'label': 'Unavailability - %',
        'limit': [0.0, 8.0]
    },
    'avg_avail': {
        'label': 'Availability - %',
        'limit': [0.0, 100.0]
    }
}

X_PARAM = {
    'probability': {
        'label': 'Elite Probability',
        'limit': [10, 90],
    }
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
        value = 100.0 * value
    elif metric == 'avg_avail':
        value = 100.0 * value
    elif metric == 'dsr':
        value = 100.0 * value

    return value


def format_field(value, field):
    value = float(value)
    if field == 'probability':
        value = round(value, 2)

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


def gen_figure(data, metric, x, x_field, data_filter, filename=None):
    plt.clf()
    matplotlib.rcParams.update({'font.size': 20})
    filtered = filter_data(data, **data_filter)

    y = []
    y_errors = []
    for x_value in x:
        x_filter = {x_field: x_value}
        x_data = filter_data(filtered, **x_filter)
        values = list(map(lambda r: format_metric(r[metric], metric), x_data))
        mean, error = calc_stats(values)
        y.append(mean)
        y_errors.append(error)
        print("{} x={:.1f}, y={:.1f}".format(metric, x_value, mean))

    x = [format_field(i, x_field) for i in x]
    plt.errorbar(x, y, yerr=y_errors, markersize=10, fmt='-o')
    plt.subplots_adjust(bottom=0.2, top=0.97, left=0.12, right=0.96)

    x_param = X_PARAM[x_field]
    y_param = Y_PARAM[metric]

    plt.xlabel(x_param['label'])
    plt.ylabel(y_param['label'])
    plt.ylim(*y_param['limit'])
    # plt.xlim(*x_param['limit'])
    plt.xticks(x)
    plt.grid(True)
    if not filename:
        plt.show()
    else:
        plt.savefig(filename, dpi=DPI, bbox_inches='tight', pad_inches=0.05)


def run():
    data = get_data_from_file('exp/output/exp_4.csv')

    all_solutions = [
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
            'title': 'ep',
            'filter': {},
            'x_field': 'probability',
            'x_values': [0.5, 0.6, 0.7000000000000001, 0.8, 0.9]
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
                filename = "exp/figs/exp_4/fig_{}_{}_{}_{}.png".format(
                    fig_title, metric, solution, sol_version
                )
                gen_figure(data, metric, x, x_field, filter, filename)


if __name__ == '__main__':
    print("Execute as 'python3 analyze.py exp_4'")
