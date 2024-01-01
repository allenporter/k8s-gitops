"""Ansible action plugin for converting a jwk key to pem.

This is used to allow a certbot jwk key to be used with ansible acme modules
that accept a pem key.
"""

from ansible.plugins.action import ActionBase
from cryptography.hazmat.primitives import serialization
import jwt
from jwt.exceptions import InvalidKeyError


def jwk_to_pem_private_key(jwk_key_content: str) -> str:
    """Return a pem private key from a jwk key."""
    try:
        private_key = jwt.algorithms.RSAAlgorithm.from_jwk(jwk_key_content)
    except InvalidKeyError as err:
        raise AnsibleError(f"Failed to decode jwk key content: {err}")

    try:
        private_key_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    except ValueError as err:
        raise AnsibleError(f"Failed to serialize private key: {err}")

    return private_key_bytes.decode("utf-8")


class FilterModule(object):
    """Ansible jinja2 filters."""

    def filters(self):
        return {"jwk_to_pem": jwk_to_pem_private_key}
