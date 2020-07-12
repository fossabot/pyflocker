from Crypto.Hash import (SHA224, SHA256, SHA384, SHA512, SHA3_224, SHA3_256,
                         SHA3_384, SHA3_512)

from .. import base


class _HashWrapper:
    def __init__(self, truncate):
        self._trunc = truncate

    def new(self, data=b''):
        return SHA512.new(data, truncate=self._trunc)


hashes = {
    'sha224': SHA224.new,
    'sha256': SHA256.new,
    'sha384': SHA384.new,
    'sha512': SHA512.new,
    'sha512_224': lambda data: SHA512.new(data, '224'),
    'sha512_256': lambda data: SHA512.new(data, '224'),
    'sha3_224': SHA3_224,
    'sha3_256': SHA3_256,
    'sha3_384': SHA3_384,
    'sha3_512': SHA3_512,
}


class Hash(base.BaseHash):
    def __init__(self, name, data=b''):
        self._hasher = hashes[name](data)

    @base.before_finalized
    def update(self, data):
        self._hasher.update(data)

    @base.finalizer(allow=True)
    def digest(self):
        return self._hasher.digest()