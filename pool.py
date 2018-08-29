from Queue import Queue
from threading import Thread


class Worker(Thread):
    """Thread executing tasks from a given tasks queue"""

    def __init__(self, tasks, output):
        Thread.__init__(self)
        self.tasks = tasks
        self.output = output
        self.daemon = True
        self.start()

    def run(self):
        while True:
            func, args, kargs = self.tasks.get()
            try:
                result = func(*args, **kargs)
                self.output.put(result)
            except Exception, e:
                print e
            self.tasks.task_done()


class ThreadPool:
    """Pool of threads consuming tasks from a queue"""

    def __init__(self, num_threads, batch_mode=False):
        self.tasks = Queue(num_threads if batch_mode else 0)
        self.output = Queue(0)
        self.workers = [Worker(self.tasks, self.output) for _ in range(num_threads)]

    def add_task(self, func, *args, **kargs):
        """Add a task to the queue"""
        self.tasks.put((func, args, kargs))

    def wait_completion(self):
        """Wait for completion of all the tasks in the queue"""
        self.tasks.join()

    def umap(self, func, tasks):
        for task in tasks:
            self.add_task(func, task)
        self.wait_completion()
        results = []
        while not self.output.empty():
            results.append(self.output.get_nowait())
            self.output.task_done()
        return results
