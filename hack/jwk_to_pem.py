"""Convert a jwk key to a pem private key."""

import argparse

from cryptography.hazmat.primitives import serialization
import jwt
from jwt.exceptions import InvalidKeyError


class DecodeError(Exception):
    """Raised when a JWT cannot be decoded."""


def jwk_to_pem_private_key(jwk_key_content: str) -> str:
    """Return a pem private key from a jwk key."""
    try:
        private_key = jwt.algorithms.RSAAlgorithm.from_jwk(jwk_key_content)
    except InvalidKeyError as err:
        raise DecodeError(f"Failed to decode jwk key content: {err}")

    try:
        private_key_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    except ValueError as err:
        raise DecodeError(f"Failed to serialize private key: {err}")

    return private_key_bytes.decode("utf-8")


def main():
    """Run the script."""

    parser = argparse.ArgumentParser(
        description="Convert a jwk key to a pem private key."
    )
    parser.add_argument(
        "jwk_key_file",
        type=argparse.FileType("r"),
        help="The jwk key file to convert.",
    )
    args = parser.parse_args()

    jwk_key_content = args.jwk_key_file.read()
    pem_private_key = jwk_to_pem_private_key(jwk_key_content)
    print(pem_private_key)


if __name__ == "__main__":
    main()
