# Python ThreadSet and ThreadManager classes

This repo contains implementations of the `ThreadSet` and `ThreadManager`
classes, which are suggested for inclusion in the CPython standard library. The
`ThreadSet` class is inspired by the class in
[Cereggii](https://dpdani.github.io/cereggii/api/ThreadSet/).  The version
implemented here has some differences (smaller API, different init signature).

The `ThreadManager` class is a context manager.  It is motivated by the
observation that it's quite easy to forget to call `join()` on threads. Looking
at the Python standard library, there are a number of different solutions to
this, such as the `test.support.threading_cleanup()` context manager.

Typical usage of these two classes would be like the following:
```
import threading

N_READERS = 4
N_WRITERS = 2

def run_threads():
    writers_done = threading.Event()

    def reader():
        while not writers_done.is_set():
            ...

    def writer():
        ...

    with threading.ThreadManager() as tm:
        readers = threading.ThreadSet(tm(reader) for _ in range(N_READERS))
        writers = threading.ThreadSet(tm(writer) for _ in range(N_WRITERS))
        (readers | writers).start()
        writers.join()
        writers_done.set()
        readers.join()
```
