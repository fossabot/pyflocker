"""Interface to hashing algorithms."""

from ..backends import load_algorithm as _load_algo


def get_available_hashes(backend=None):
    """Returns all available hashes supported by backend."""
    if backend is not None:
        return set(_load_algo("Hash", backend).hashes.keys())

    from ..backends import Backends

    algos = set()
    for bknd in list(Backends):
        algos.update(set(_load_algo("Hash", bknd).hashes.keys()))
    return algos


def new(hashname, data=b"", digest_size=None, *, backend=None):
    """
    Instantiate a new hash instance `hashname` with initial
    data `data` (default is empty `bytes`).
    The Hash object created by this function can be used as
    the `hash` argument to OAEP and MGF1.

    Args:
        hashname: Name of the hashing function to use.
        data: Initial data to pass to hashing function.
        digest_size:
            The length of the digest from the hash function.
            Required for Blake and Shake.

    Kwargs:
        backend:
            The backend to use. It must be a value from `Backends`.

    Returns:
        A Hash interface with the given hashing algorithm.

    Raises:
        KeyError if the hashing function is not supported.
    """
    return _load_algo("Hash", backend).Hash(
        hashname,
        data,
        digest_size=digest_size,
    )
