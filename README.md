# Service Placement Offline

## Init
1. Install Cplex Studio
2. Setup Cplex Python API located in the folder `yourCPLEXhome/cplex/python/VERSION/PLATFORM/`
```sh
$ python setup.py install
```
3. Add `yourCPLEXhome/cplex/python/VERSION/PLATFORM/` in the environment variable `PYTHONPATH`, if necessary
4. Install required packages
```sh
$ pip install -r requirements.txt
```

## Execute Experiments
```sh
$ time python main.py exp_1
$ time python main.py exp_2
$ time python main.py exp_n param_1 param_2 ...
```

## Execute Tests
```sh
$ time python test.py exp_1
$ time python test.py exp_2
$ time python test.py exp_n param_1 param_2 ...
```


## Generate Figures
```sh
$ python analyze.py
```

## Documentations
- [DOcplex Modeling for Python](https://developer.ibm.com/docloud/documentation/optimization-modeling/modeling-for-python/)
- [NumPy](https://docs.scipy.org/doc/numpy/reference/index.html)
- [SciPy Statistical functions](https://docs.scipy.org/doc/scipy/reference/stats.html)
- [Matplot](https://matplotlib.org/)
- [Pathos Multiprocessing](https://pathos.readthedocs.io/en/latest/pathos.html)
- [Hexagonal Grids](https://www.redblobgames.com/grids/hexagons/)
