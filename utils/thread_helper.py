import threading


def api_call_limited_parallel(func, args_list, max_threads=10):
    def worker(sem, func, *args):
        with sem:
            func(*args)

    sem = threading.Semaphore(max_threads)

    threads = []
    for i in range(len(args_list)):
        args = args_list[i]
        t = threading.Thread(target=worker, args=(sem, func, *args))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()
