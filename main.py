import sys


def exp_1(args=[]):
    import exp.exp_1
    exp.exp_1.run()


def exp_2(args=[]):
    import exp.exp_2
    exp.exp_2.run()


def exp_3(args=[]):
    import exp.exp_3
    exp.exp_3.run()


if __name__ == '__main__':
    args = sys.argv[1:]
    experiment = args[0] if args else 'exp_1'
    if experiment in locals():
        exp_func = locals()[experiment]
        exp_func(args[1:])
