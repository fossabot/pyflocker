try:
    from Cryptodome.Hash import (
        SHA224,
        SHA256,
        SHA384,
        SHA512,
        SHA3_224,
        SHA3_256,
        SHA3_384,
        SHA3_512,
        BLAKE2b,
        BLAKE2s,
        SHAKE128,
        SHAKE256,
    )
except ModuleNotFoundError:
    from Crypto.Hash import (
        SHA224,
        SHA256,
        SHA384,
        SHA512,
        SHA3_224,
        SHA3_256,
        SHA3_384,
        SHA3_512,
        BLAKE2b,
        BLAKE2s,
        SHAKE128,
        SHAKE256,
    )

from .. import base

hashes = {
    'sha224': SHA224.new,
    'sha256': SHA256.new,
    'sha384': SHA384.new,
    'sha512': SHA512.new,
    'sha512_224': lambda data=b'': SHA512.new(data, '224'),
    'sha512_256': lambda data=b'': SHA512.new(data, '256'),
    'sha3_224': SHA3_224.new,
    'sha3_256': SHA3_256.new,
    'sha3_384': SHA3_384.new,
    'sha3_512': SHA3_512.new,
}

arbitrary_digest_size_hashes = {
    'blake2b': BLAKE2b.new,
    'blake2s': BLAKE2s.new,
    'shake128': SHAKE128.new,
    'shake256': SHAKE256.new,
}

xofs = {
    'shake128': SHAKE128.new,
    'shake256': SHAKE256.new,
}

hashes.update(arbitrary_digest_size_hashes)


class Hash(base.BaseHash):
    def __init__(self, name, data=b'', *, digest_size=None):
        self._digest_size = digest_size
        _hash = hashes[name]

        if digest_size is None:
            if name in arbitrary_digest_size_hashes:
                raise ValueError('value of digest-size is required')

        if name in arbitrary_digest_size_hashes.keys() ^ xofs.keys():
            self._hasher = _hash(data=data, digest_bytes=digest_size)
        else:
            self._hasher = _hash(data)
        self._name = name

    @property
    def digest_size(self):
        try:
            return self._hasher.digest_size
        except AttributeError:  # for SHAKE
            return self._digest_size

    @property
    def block_size(self):
        """Block size of the underlying hash algorithm."""
        try:
            return self._hasher.block_size
        except AttributeError:
            raise AttributeError(
                f'Hash algorithm {self.name} does not '
                'have block_size parameter.'
            ) from None

    @property
    def name(self):
        return self._name

    @property
    def oid(self):
        """ASN.1 Object ID of the hash algorithm."""
        try:
            return self._hasher.oid
        except AttributeError:
            # for BLAKE-2b/2s
            raise AttributeError(
                'oid is avaliable only for digest sizes 20, 32, 48 and 64')

    @base.before_finalized
    def update(self, data):
        self._hasher.update(data)

    @base.before_finalized
    def copy(self):
        hashobj = Hash(self.name, digest_size=self.digest_size)
        try:
            hashobj._hasher = self._hasher.copy()
        except AttributeError:
            raise AttributeError(
                f'Hash {self.name} does not support copying.'
            ) from None
        return hashobj

    @base.finalizer(allow=True)
    def digest(self):
        if self._name in xofs:
            return self._hasher.read(self._digest_size)
        return self._hasher.digest()

    def new(self, data=b'', *, digest_size=None):
        return type(self)(
            self.name,
            data,
            digest_size=digest_size or self.digest_size,
        )
