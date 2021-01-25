"""Base classes for pyflocker."""

from __future__ import annotations

import sys
import typing

from functools import wraps, partial
from abc import ABCMeta, abstractmethod

from . import exc


class BaseSymmetricCipher(metaclass=ABCMeta):
    @abstractmethod
    def is_encrypting(self) -> bool:
        """Whether the cipher is encrypting or not.

        Returns:
            bool: True if encrypting, else False.
        """


class BaseNonAEADCipher(BaseSymmetricCipher):
    @abstractmethod
    def update(self, data: typing.ByteString) -> bytes:
        """Takes bytes-like object and returns encrypted/decrypted
        bytes object.

        Args:
            data (bytes, bytesarray):
                The bytes-like object to pass to the cipher.

        Returns:
            bytes: bytes-like encrypted data.
        """

    @abstractmethod
    def update_into(
        self,
        data: typing.ByteString,
        out: typing.ByteString,
    ) -> None:
        """Encrypt or decrypt the `data` and store it in a preallocated buffer
        `out`.

        Args:
            data (bytes, bytearray, memoryview):
                The bytes-like object to pass to the cipher.
            out (bytearray, memoryview):
                The buffer interface where the encrypted/decrypted data
                must be written into.
        """

    @abstractmethod
    def finalize(self) -> None:
        """Finalizes and closes the cipher.

        Raises:
            AlreadyFinalized: If the cipher was already finalized.
        """


class BaseAEADCipher(BaseSymmetricCipher):
    """Abstract base class for AEAD ciphers.

    Custom cipher wrappers that provide AEAD functionality to NonAEAD
    ciphers must derive from this.
    """

    @abstractmethod
    def update(self, data: typing.ByteString) -> bytes:
        """Takes bytes-like object and returns encrypted/decrypted
        bytes object, while passing it through the MAC.

        Args:
            data (bytes, bytesarray, memoryview):
                The bytes-like object to pass to the cipher.

        Returns:
            bytes: bytes-like encrypted data.
        """

    @abstractmethod
    def update_into(
        self,
        data: typing.ByteString,
        out: typing.ByteString,
    ) -> None:
        """Encrypt or decrypt the `data` and store it in a preallocated buffer
        `out`. The data is authenticated internally.

        Args:
            data (bytes, bytearray, memoryview):
                The bytes-like object to pass to the cipher.
            out (bytearray, memoryview):
                The buffer interface where the encrypted/decrypted data
                must be written into.
        """

    @abstractmethod
    def authenticate(self, data: typing.ByteString) -> None:
        """Authenticates part of the message that get deliverd as is, without
        any encryption.

        Args:
            data (bytes, bytearray, memoryview):
                The bytes-like object that must be authenticated.

        Raises:
            TypeError:
                if this method is called after calling
                :py:attr:`~BaseAEADCipher.update`.
        """

    @abstractmethod
    def finalize(self, tag: typing.Optional[typing.ByteString] = None) -> None:
        """Finalizes and ends the cipher state.

        Args:
            tag (bytes, bytearray):
                The associated tag that authenticates the decryption.
                `tag` is required for decryption only.

        Raises:
            ValueError: If cipher is decrypting and tag is not supplied.
            DecryptionError: If the decryption was incorrect.
        """

    @abstractmethod
    def calculate_tag(self) -> typing.Optional[bytes]:
        """Calculates and returns the associated `tag`.

        Returns:
            Union[None, bytes]:
                Returns None if decrypting, otherwise the associated
                authentication tag.
        """


class BaseHash(metaclass=ABCMeta):
    """Abstract base class for hash functions. Follows PEP-0452.

    Custom MACs must use this interface.
    """

    @property
    @abstractmethod
    def digest_size(self) -> int:
        """
        The size of the digest produced by the hashing object, measured in
        bytes. If the hash has a variable output size, this output size must
        be chosen when the hashing object is created, and this attribute must
        contain the selected size. Therefore, None is not a legal value for
        this attribute.

        Returns:
            int: Digest size as integer.
        """

    @property
    @abstractmethod
    def block_size(self) -> typing.Union[int, NotImplemented]:
        """
        An integer value or NotImplemented; the internal block size of the hash
        algorithm in bytes. The block size is used by the HMAC module to pad
        the secret key to digest_size or to hash the secret key if it is longer
        than digest_size. If no HMAC algorithm is standardized for the hash
        algorithm, returns ``NotImplemented`` instead.

        See Also:
            PEP 452 -- API for Cryptographic Hash Functions v2.0,
            https://www.python.org/dev/peps/pep-0452

        Returns:
            Union[int, NotImplemented]:
                An integer if block size is available, otherwise
                ``NotImplemented``
        """

    @abstractmethod
    def update(self, data: typing.ByteString) -> None:
        """
        Hash string into the current state of the hashing object. ``update()``
        can be called any number of times during a hashing object's lifetime.

        Args:
            data (bytes, bytearray, memoryview):
                The chunk of message being hashed.

        Raises:
            AlreadyFinalized:
                This is raised if ``digest`` or ``hexdigest`` has been called.
        """

    @abstractmethod
    def digest(self) -> bytes:
        """
        Return the hash value of this hashing object as a string containing
        8-bit data. The object is not altered in any way by this function; you
        can continue updating the object after calling this function.

        Returns:
            bytes: Digest as binary form.
        """

    def hexdigest(self) -> str:
        """
        Return the hash value of this hashing object as a string containing
        hexadecimal digits.

        Returns:
            str: Digest, as a hexadecimal form.
        """
        return self.digest().hex()

    @abstractmethod
    def copy(self) -> BaseHash:
        """
        Return a separate copy of this hashing object.
        An update to this copy won't affect the original object.

        Returns:
            BaseHash: a copy of hash function.

        Raises:
            AlreadyFinalized:
                This is raised if the method is called after calling
                `~BaseHash.digest` method.
        """

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the hash function.

        Returns:
            str: Name of hash function.
        """

    def __repr__(self) -> str:
        return f"<{type(self).__name__} '{self.name}' at {hex(id(self))}>"
