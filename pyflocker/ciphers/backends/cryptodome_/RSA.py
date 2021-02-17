from __future__ import annotations

import typing

from Cryptodome.PublicKey import RSA

from ... import base, exc
from ..asymmetric import OAEP, PSS
from ._serialization import encodings, formats, protection_schemes
from .asymmetric import get_padding


class _RSAKey:
    @property
    def n(self):
        return self._key.n

    @property
    def e(self):
        return self._key.e


class RSAPrivateKey(_RSAKey, base.BasePrivateKey):
    """RSA private key wrapper class."""

    def __init__(self, n: int, e: int = 65537, **kwargs):
        if kwargs:
            self._key = kwargs.pop("key")
        else:
            self._key = RSA.generate(n, e=e)

    @property
    def p(self) -> int:
        """First factor of RSA modulus."""
        return self._key.p

    @property
    def q(self) -> int:
        """Second factor of RSA modulus."""
        return self._key.q

    @property
    def d(self) -> int:
        """RSA private exponent."""
        return self._key.d

    @property
    def u(self) -> int:
        """Chinese remainder exponent.

        (p ** -1) % q
        """
        return self._key.u

    def decryptor(self, padding=OAEP()) -> _EncDecContext:
        """Creates a decryption context.

        Args:
            padding: The padding to use. Default is OAEP.

        Returns:
            _EncDecContext: object for decrypting ciphertexts.
        """
        return _EncDecContext(True, get_padding(padding)(self._key, padding))

    def signer(self, padding=PSS()) -> _SigVerContext:
        """Create a signer context.

        Args:
            padding: The padding to use. Default is PSS.

        Returns:
            _SigVerContext: Signer object for signing messages.

        Note:
            If the padding is PSS and ``salt_length`` is None, the salt length
            will be maximized, as in OpenSSL.
        """
        return _SigVerContext(True, get_padding(padding)(self._key, padding))

    def public_key(self) -> RSAPublicKey:
        """Creates a public key from the private key.

        Returns:
            RSAPublicKey: The RSA public key.
        """
        return RSAPublicKey(self._key.publickey())

    def serialize(
        self,
        encoding: str = "PEM",
        format: str = "PKCS8",
        passphrase: typing.ByteString = None,
        *,
        protection: str = None,
    ) -> bytes:
        """Serialize the private key.

        Args:
            encoding (str):
                PEM or DER (defaults to PEM).
            format (str):
                PKCS1 or PKCS8 (defaults to PKCS8).
            passphrase (bytes, bytearray, memoryview):
                a bytes object to use for encrypting the private key.
                If ``passphrase`` is None, the private key will be exported
                in the clear!

        Keyword Arguments:
            protection (str):
                The protection scheme to use.

                Supplying a value for protection has meaning only if the
                ``format`` is PKCS8. If ``None`` is provided
                ``PBKDF2WithHMAC-SHA1AndAES256-CBC`` is used as the protection
                scheme.

        Returns:
            bytes: Serialized key as a bytes object.

        Raises:
            ValueError:
                If the encoding is incorrect or, if DER is used with PKCS1 or
                protection value is supplied with PKCS1 format.
            KeyError: if the format is invalid or not supported.
        """
        if encoding not in encodings.keys() ^ {"OpenSSH"}:
            raise ValueError("encoding must be PEM or DER")

        if protection is not None:
            if protection not in protection_schemes:
                raise ValueError("invalid protection scheme")

        if format == "PKCS1":
            if protection is not None:
                raise ValueError("protection is meaningful only for PKCS8")
            if encoding == "DER":
                raise ValueError("cannot use DER with PKCS1 format")

        if passphrase is not None and protection is None:
            # use a curated encryption choice and not DES-EDE3-CBC
            protection = "PBKDF2WithHMAC-SHA1AndAES256-CBC"

        return self._key.export_key(
            format=encodings[encoding],
            pkcs=formats[format],
            passphrase=(
                memoryview(passphrase).tobytes()
                if passphrase is not None
                else None
            ),
            protection=protection,
        )

    @classmethod
    def load(
        cls,
        data: typing.ByteString,
        password: typing.ByteString = None,
    ) -> RSAPrivateKey:
        """Loads the private key as `bytes` object and returns the
        Key interface.

        Args:
            data (bytes):
                The key as bytes object.
            password (bytes, bytearray, memoryview):
                The password that deserializes the private key. `password`
                must be a `bytes` object if the key was encrypted while
                serialization, otherwise `None`.

        Returns:
            :any:`RSAPrivateKey`: `RSAPrivateKey` key object.

        Raises:
            ValueError: if the key could not be deserialized.
        """
        try:
            key = RSA.import_key(data, password)
            if not key.has_private():
                raise ValueError("The key is not a private key")
            return cls(None, key=key)
        except ValueError as e:
            raise ValueError(
                "Cannot deserialize key. "
                "Either Key format is invalid or "
                "password is missing or incorrect.",
            ) from e


class RSAPublicKey(_RSAKey, base.BasePublicKey):
    """RSA Public Key wrapper class."""

    def __init__(self, key):
        self._key = key

    def encryptor(self, padding=OAEP()) -> _EncDecContext:
        """Creates a encryption context.

        Args:
            padding: The padding to use. Defaults to OAEP.

        Returns:
            :any:`RSAEncryptionCtx`:
                An `RSAEncryptionCtx` encryption context object.
        """
        return _EncDecContext(False, get_padding(padding)(self._key, padding))

    def verifier(self, padding=PSS()) -> _SigVerContext:
        """Creates a verifier context.

        Args:
            padding: The padding to use. Defaults to ECC.

        Returns:
            _SigVerContext: verifier object for verification.

        Note:
            If the padding is PSS and ``salt_length`` is None, the salt length
            will be maximized, as in OpenSSL.
        """
        return _SigVerContext(False, get_padding(padding)(self._key, padding))

    def serialize(self, encoding: str = "PEM") -> bytes:
        """Serialize the private key.

        Args:
            encoding (str): PEM, DER or OpenSSH (defaults to PEM).

        Returns:
            bytes: The serialized public key as bytes object.

        Raises:
            KeyError: if the encoding is not supported or invalid.
        """
        return self._key.export_key(format=encodings[encoding])

    @classmethod
    def load(cls, data: typing.ByteString) -> RSAPublicKey:
        """Loads the public key as `bytes` object and returns the
        Key interface.

        Args:
            data (bytes):
                The key as bytes object.

        Returns:
            RSAPublicKey: The public key.

        Raises:
            ValueError: if the key could not be deserialized.
        """
        try:
            key = RSA.import_key(data)
            if key.has_private():
                raise ValueError("The key is not a public key")
            return cls(key=key)
        except ValueError as e:
            raise ValueError(
                "Cannot deserialize key. Key format might be invalid."
            ) from e


class _EncDecContext:
    def __init__(self, is_private, ctx):
        self._is_private = is_private
        self._ctx = ctx

    def encrypt(self, data):
        return self._ctx.encrypt(data)

    def decrypt(self, data):
        if not self._is_private:
            raise TypeError("Only private keys can decrypt ciphertexts.")
        try:
            return self._ctx.decrypt(data)
        except ValueError as e:
            raise exc.DecryptionError from e


class _SigVerContext:
    def __init__(self, is_private, ctx):
        self._is_private = is_private
        self._ctx = ctx

    def sign(self, msghash):
        if not self._is_private:
            raise TypeError("Only private keys can sign messages.")
        return self._ctx.sign(msghash)

    def verify(self, msghash, signature):
        if not self._ctx.verify(msghash, signature):
            raise exc.SignatureError
