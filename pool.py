from Queue import Queue
from threading import Thread
import time


class Worker(Thread):
    """Thread executing tasks from a given tasks queue"""

    def __init__(self, tasks, output, name=""):
        Thread.__init__(self)
        self.tasks = tasks
        self.output = output
        self.daemon = True
        self.name = name
        self.start()

    def run(self):
        while True:
            func, args, kargs = self.tasks.get()
            try:
                # print("start {}".format(self.name))
                start_time = time.time()
                result = func(*args, **kargs)
                self.output.put(result)
                elapsed_time = time.time() - start_time
                # print("end {} - {} - {}".format(self.name, elapsed_time, self.tasks.qsize()))
            except Exception, e:
                print e
            self.tasks.task_done()


class ThreadPool:
    """Pool of threads consuming tasks from a queue"""

    def __init__(self, num_threads, batch_mode=False):
        self.num_threads = num_threads
        self.batch_mode = batch_mode
        self.tasks = Queue(num_threads if batch_mode else 0)
        self.output = Queue(0)
        self.workers = [Worker(self.tasks, self.output, name="worker_{}".format(i)) for i in range(num_threads)]

    def add_task(self, func, *args, **kargs):
        """Add a task to the queue"""
        self.tasks.put((func, args, kargs))

    def wait_completion(self):
        """Wait for completion of all the tasks in the queue"""
        self.tasks.join()

    def map(self, func, args_list):
        """ Add a list of tasks to the queue """
        start_time = time.time()
        for args in args_list:
            self.add_task(func, args)
        self.wait_completion()
        results = []
        while not self.output.empty():
            results.append(self.output.get_nowait())
            self.output.task_done()
        elapsed_time = time.time() - start_time
        print(elapsed_time)
        return results
