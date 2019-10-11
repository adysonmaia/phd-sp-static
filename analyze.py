import sys


def exp_1(args=[]):
    import exp.analyze_1
    exp.analyze_1.run()


def exp_2(args=[]):
    import exp.analyze_2
    exp.analyze_2.run()


def exp_3(args=[]):
    import exp.analyze_3
    exp.analyze_3.run()


def exp_4(args=[]):
    import exp.analyze_4
    exp.analyze_4.run()


def exp_5(args=[]):
    import exp.analyze_5
    exp.analyze_5.run()


if __name__ == '__main__':
    args = sys.argv[1:]
    experiment = args[0] if args else 'exp_1'
    if experiment in locals():
        exp_func = locals()[experiment]
        exp_func(args[1:])
