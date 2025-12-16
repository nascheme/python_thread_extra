from __future__ import annotations
from threading import Thread
from typing import Any, Callable, Iterable, Self


class ThreadSet:
    """A container for sets of threads."""

    def __init__(self, threads: Iterable[Thread] = ()) -> None:
        self._threads: set[Thread] = set(threads)

    def start(self) -> None:
        """Start all of the threads in the set."""
        for t in self._threads:
            t.start()

    def join(self, timeout: float | None = None) -> None:
        """Join all of the threads in the set."""
        for t in self._threads:
            t.join(timeout)

    def start_and_join(self, join_timeout: float | None = None) -> None:
        """Start the threads in this set, then join them."""
        self.start()
        self.join(join_timeout)

    def is_alive(self) -> Iterable[bool]:
        """Call Thread.is_alive() for each thread in the set and return
        an iterator of those values."""
        return (t.is_alive() for t in self._threads)

    def __or__(self, other) -> Self:
        """Returns a new set containing all the threads in the operands,
        which must be ThreadSet instances.
        """
        if not isinstance(other, self.__class__):
            raise TypeError(
                f"cannot make union of {self.__class__} and {other!r}"
            )
        return self.__class__(self._threads | other._threads)

    def __ior__(self, other) -> Self:
        """Adds the threads in the right operand into this set. The right
        operand must be a ThreadSet.
        """
        if not isinstance(other, self.__class__):
            raise TypeError(
                f"cannot make union of {self.__class__} and {other!r}"
            )
        self._threads |= other._threads
        return self

    def __len__(self) -> int:
        """Returns the number of threads contained in this set."""
        return len(self._threads)


class ThreadManager:
    """A context manager for creating threads and ensuring they are
    joined when the manager is exited.

    Example usage:

        writers_done = threading.Event()
        with threading.ThreadManager() as tm:
            readers = threading.ThreadSet(tm(reader) for _ in range(N_READERS))
            writers = threading.ThreadSet(tm(writer) for _ in range(N_WRITERS))
            (readers | writers).start()
            writers.join()
            writers_done.set()
            readers.join()
    """

    THREAD_CLASS: type[Thread] = Thread

    def __init__(self, /, join_timeout: float | None = None) -> None:
        self._join_timeout = join_timeout
        self._threads: list[Thread] = []

    def __call__(
        self, target: Callable, /, *args: Any, **kwargs: Any
    ) -> Thread:
        """Create and return a new Thread.  The first argument is the target
        function.  The rest of the arguments are passed along to the target.
        """
        thread = self.THREAD_CLASS(target=target, args=args, kwargs=kwargs)
        self._threads.append(thread)
        return thread

    def create_thread(self, *args: Any, **kwargs: Any) -> Thread:
        """Create and return a new Thread instance.  Arguments are
        passed to the Thread init method.
        """
        thread = self.THREAD_CLASS(*args, **kwargs)
        self._threads.append(thread)
        return thread

    def __enter__(self) -> None:
        pass

    def __exit__(self, *args) -> None:
        for thread in self._threads:
            if thread.is_alive():
                thread.join(self._join_timeout)
