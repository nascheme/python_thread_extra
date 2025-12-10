# Python ThreadSet and ThreadManager classes

## Overview

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

## API Design Q & A

Here are some notes about the API design, in the form of questions and answers.
The design is not fixed yet so feel free to argue for design changes.

* *What should be the arguments to the `ThreadSet` init?*  Cereggii takes an
  optional number of arguments (`*args`) whereas the `set` built-in takes a
  single argument that is an iterable.  I think following `set` is better.
  It seems likely the sets will mostly be created from generator expressions.

* *Should we include some additional methods and class methods that Cereggii's
  `ThreadSet` provides?*  I'd like to start with the minimal API possible and
  then only extend if we have a clear need.  Once an API is added to the
  CPython standard library, it is very hard to change.

* *What should the case of these names be, e.g. camel case or something else?*
  I think these classes should be added to the `threading` module and the names
  should fit with the existing class names in that file.  So, camel case.

* *What should the name of the context manager be?*  There are many choices.  Rust
  has a similar thing and they call it `thread::scope`.  In Python, scope
  generally doesn't mean context manager and so that doesn't seem a good name.
  We could use `ThreadContext` but I fear that could be confusing with context
  variables.  So, my choice is `ThreadManager` with the conventional local
  variable being `tm`.  Another idea would be to use the term "nursery" since
  this is quite similar to Trio's concept of that.

* *How should the context manager join the threads by default, should it use
  a default timeout?*  I'm not sure about this but using a timeout raises the
  hard question about what timeout would be appropriate.  Looking at Rust's
  scope, it doesn't use a timeout.  Looking elsewhere in Python's stdlib, there
  are other similar context managers, especially in the unit test suite, that do
  set a default timeout.  I think `ThreadManager` should grow an optional
  `join_timeout` keyword.  That way, if the context exits due to an exception
  the timeout would be used.

* *What APIs should be provided for creating threads?*  The Cereggii's `ThreadSet`
  class has class methods like `range()` and `repeat()`.  I prefer that the
  manager creates the threads because it needs to clean them up later.
  Creating threads by passing a "target" function is the most common way and so
  there should be a concise way to do that.   I'm using `__call__` with the same
  signature as `ThreadPoolExecutor.submit()`.  I also provide `create_thread()`
  with the same signature as the `Thread()` class.  Maybe this is unneeded
  flexibility and we should remove `create_thread()`?

* *Should the `ThreadSet` somehow require that contained threads are within a
  context manager (so we can ensure they are joined)?*  I think this is not
  needed.  It would be valid (if a bit dangerous) to use the `ThreadSet` class
  outside of the context manager.  Since the manager is creating the threads,
  it should be responsible for cleaning them (joining).  As long as you don't
  create threads by calling `Thread()` directly, you are safe.

* *Should we consider that `ThreadSet` and `ThreadManager` will later be
  implemented in C?*  I think it's unlikely given that even with huge machines
  we are unlikely to have sets that contain more than a few thousand items.
  If that ever becomes a problem, a C version of the class should be possible
  but I don't think it needs to be a design consideration.  Simple and
  idiomatic Python code should be the goal.

* *Should `ThreadManager` provide a way to create a thread set, e.g. via a
  method?*  I'm not sure but I don't think it adds much value.  You could
  make code more concise by adding a short method name for this, e.g.
  `tm.set(...)`.  You could also avoid generator expressions by adding
  methods similar to Cereggii's `range()` and `repeat()` class methods.
  However, I find an explicit generator expression to be fairly concise
  and it's more clear what's happening.  We could add methods like this
  later, if they seem useful.

* *Should `ThreadManager` do some more complex or graceful cleanup of threads?*
  I'm not sure about this one.  If you look at what `ThreadPoolExecutor` or
  what `test.support.threading_helper` does then perhaps we should do more
  to try to gracefully cleanup the threads.  Right now, the manager only does
  `join()` on all of the started threads.  If there is an exception "half-way"
  into the execution of the context body, it seems pretty likely threads could
  be left in a blocked state (e.g. waiting on a condition that's never going to
  happen).  I feel like trying to do more than just call `join()` is overly
  ambitious and the manager doesn't really know how to gracefully cleanup for
  those states.  So, its only job is to ensure that threads created by the
  manager are joined when the context is exited.
