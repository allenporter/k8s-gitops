"""Validates that all files in the repo are valid kustomizations."""

from __future__ import annotations

import asyncio
import pytest
import datetime
import os
from pathlib import Path
import subprocess
import logging
import yaml
from functools import cache
from typing import Generator, Any

from scripts.manifest import cmd


_LOG_FMT = (
    "%(asctime)s.%(msecs)03d %(levelname)s (%(threadName)s) [%(name)s] %(message)s"
)
logging.basicConfig(format=_LOG_FMT)

_LOGGER = logging.getLogger(__name__)


# Note: We should really only build policies included in the kustomize build, similar
# to how we manage helm releases.
POLICY_DIR = "infrastructure/base/policies"


HELMREPO_KINDS = {("HelmRepository", "source.toolkit.fluxcd.io/v1beta2")}
HELMRELEASE_KINDS = {("HelmRelease", "helm.toolkit.fluxcd.io/v2beta1")}


@pytest.fixture(scope="module")
def event_loop(request):
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True, scope="session")
def yaml_hack() -> None:
    """Hack for prometheus operator yaml.

    See:
      https://github.com/yaml/pyyaml/pull/635
      https://github.com/yaml/pyyaml/issues/89
      https://github.com/prometheus-operator/prometheus-operator/issues/4955
    """
    yaml.constructor.SafeConstructor.add_constructor(
        "tag:yaml.org,2002:value", yaml.constructor.SafeConstructor.construct_yaml_str
    )


# TODO: Move to kyverno
ALLOWED_INGRESS_ANNOTATIONS = {
    "cert-manager.io/cluster-issuer",
    "external-dns.alpha.kubernetes.io/hostname",
    "external-dns.alpha.kubernetes.io/target",
    "hajimari.io/icon",
    "hajimari.io/appName",
    "haproxy.org/server-ssl",
    "haproxy.org/forwarded-for",
    "kubernetes.io/ingress.class",
    "nginx.ingress.kubernetes.io/backend-protocol",
    "service.alpha.kubernetes.io/app-protocols",
}
