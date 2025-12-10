# Example inspired by unit test in the py-radix package

import ipaddress
import random
import threading

import radix


rand = random.Random(0x4D3D3D3)


def random_address(network):
    host_bits = 32 - network.prefixlen
    random_bits = rand.randint(0, 2**host_bits - 1)
    random_ip_int = int(network.network_address) + random_bits
    return ipaddress.IPv4Address(random_ip_int)


def random_network():
    # leave at least 4 bits of randomness for network addresses
    masklen = rand.randint(0, 28)
    network_int = rand.randint(0, 2**masklen - 1)
    return ipaddress.IPv4Network((network_int << (32 - masklen), masklen))


def chunks(seq, size):
    return (set(seq[pos : pos + size]) for pos in range(0, len(seq), size))


def test_multithreaded_radix():
    networks = [random_network() for _ in range(100)]
    address_lists = [
        [random_address(network) for _ in range(10)] for network in networks
    ]
    # flatten
    addresses = [
        str(address) for addresses in address_lists for address in addresses
    ]

    n_writers = 2
    n_readers = 4
    n_threads = n_writers + n_readers
    b = threading.Barrier(n_threads)

    random.shuffle(addresses)
    reader_chunks = list(chunks(addresses, len(addresses) // n_readers))

    random.shuffle(addresses)
    writer_chunks = list(chunks(addresses, len(addresses) // n_writers))

    r = radix.Radix()
    writers_done = threading.Event()

    def writer_target(i):
        addresses = writer_chunks[i]
        b.wait()
        for address in addresses:
            r.add(address)

    def reader_target(i):
        addresses = reader_chunks[i]
        b.wait()
        while not writers_done.is_set():
            for address in addresses:
                node = r.search_exact(address)
                if node and node.network == address:
                    node.data.setdefault('id', i)

    with threading.ThreadManager() as tm:
        writers = threading.ThreadSet(
            tm(writer_target, i) for i in range(n_writers)
        )
        readers = threading.ThreadSet(
            tm(reader_target, i) for i in range(n_readers)
        )

        # spawn thread pools for readers and writers, joining readers
        # after writers have finished filling the table.
        # we want reads to happen concurrently with writes to encourage races
        (readers | writers).start()
        writers.join()
        writers_done.set()
        readers.join()

    for node in r:
        written_id = node.data.get('id', None)
        if written_id:
            assert node.network in reader_chunks[node.data['id']]
