# Based on Lib/test/test_free_threading/test_list.py

import threading
from unittest import TestCase

from test.support import threading_helper


NTHREAD = 10
OBJECT_COUNT = 5_000


@threading_helper.requires_working_threading()
class TestList(TestCase):
    def test_racing_iter_append(self):
        l = []

        barrier = threading.Barrier(NTHREAD + 1)

        def writer_func(l):
            barrier.wait()
            for i in range(OBJECT_COUNT):
                l.append(C(i + OBJECT_COUNT))

        def reader_func(l):
            barrier.wait()
            while True:
                count = len(l)
                for i, x in enumerate(l):
                    self.assertEqual(x.v, i + OBJECT_COUNT)
                if count == OBJECT_COUNT:
                    break

        with threading.ThreadManager() as tm:
            writer = tm(writer_func, l)
            readers = tm.create_set(NTHREAD, reader_func, l)
            writer.start()
            readers.start()
