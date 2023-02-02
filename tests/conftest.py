"""Validates that all files in the repo are valid kustomizations."""

from __future__ import annotations

import asyncio
import pytest
import datetime
import git
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


HELMREPO_KINDS = {("HelmRepository", "source.toolkit.fluxcd.io/v1beta2")}
HELMRELEASE_KINDS = {("HelmRelease", "helm.toolkit.fluxcd.io/v2beta1")}

# Allow all API resources with these versions
ALLOWED_API_VERSIONS = {
    "v1",
    "apps/v1",
    "batch/v1",
    "monitoring.grafana.com/v1alpha1",
    "monitoring.coreos.com/v1",
}

# Allow specific API resources with specific versions
ALLOWED_API_RESOURCES = (
    HELMREPO_KINDS
    | HELMRELEASE_KINDS
    | {
        ("Alert", "notification.toolkit.fluxcd.io/v1beta2"),
        ("CephCluster", "ceph.rook.io/v1"),
        ("ClusterIssuer", "cert-manager.io/v1"),
        ("ClusterRole", "rbac.authorization.k8s.io/v1"),
        ("ClusterRoleBinding", "rbac.authorization.k8s.io/v1"),
        ("CustomResourceDefinition", "apiextensions.k8s.io/v1"),
        ("CronJob", "batch/v1beta1"),
        ("EnvoyFilter", "networking.istio.io/v1alpha3"),
        ("GitRepository", "source.toolkit.fluxcd.io/v1beta2"),
        ("HorizontalPodAutoscaler", "autoscaling/v2"),
        ("Ingress", "networking.k8s.io/v1"),
        ("IngressClass", "networking.k8s.io/v1"),
        ("IPAddressPool", "metallb.io/v1beta1"),
        ("L2Advertisement", "metallb.io/v1beta1"),
        ("MutatingWebhookConfiguration", "admissionregistration.k8s.io/v1"),
        ("PodDisruptionBudget", "policy/v1beta1"),
        ("PodDisruptionBudget", "policy/v1"),
        ("PodMonitor", "monitoring.coreos.com/v1"),
        ("PodSecurityPolicy", "policy/v1beta1"),
        ("NetworkPolicy", "networking.k8s.io/v1"),
        ("PrometheusRule", "monitoring.coreos.com/v1"),
        ("Provider", "notification.toolkit.fluxcd.io/v1beta2"),
        ("Role", "rbac.authorization.k8s.io/v1"),
        ("RoleBinding", "rbac.authorization.k8s.io/v1"),
        ("ServiceMonitor", "monitoring.coreos.com/v1"),
        ("StorageClass", "storage.k8s.io/v1"),
        ("VolumeSnapshot", "snapshot.storage.k8s.io/v1"),
        ("VolumeSnapshotClass", "snapshot.storage.k8s.io/v1"),
        ("ValidatingWebhookConfiguration", "admissionregistration.k8s.io/v1"),
    }
)


@pytest.fixture(scope="module")
def event_loop(request):
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


def kind_filter(kinds: set[tuple[str, str]]):
    """Return a yaml doc filter for specified resource type and version."""

    def func(doc):
        return (doc.get("kind"), doc.get("apiVersion")) in kinds

    return func


async def kustomize_build(filename: Path) -> str:
    """Return kustomize build and return the string contents."""
    command = ["kustomize", "build", str(filename)]
    command.extend(KUSTOMIZE_FLAGS)
    return await cmd.run_command(command)


async def kustomize_build_resources(filename: Path) -> list[dict[str, Any]]:
    """Run kustomize build and return the parsed objects."""
    doc_contents = await kustomize_build(filename)
    return list(yaml.safe_load_all(doc_contents))


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


def is_k8s(resource: dict[str, Any]) -> bool:
    """Return true if the object is a kubernetes resource."""
    assert resource
    return "kind" in resource and "apiVersion" in resource


def kind(resource: dict[str, Any]) -> tuple[str, str]:
    """Function to return the kind of a resource."""
    return (resource["kind"], resource["apiVersion"])


def is_resource_allowed(resource: dict[str, Any]) -> bool:
    """Validate the resource is allowed."""
    key = kind(resource)
    return key in ALLOWED_API_RESOURCES or key[1] in ALLOWED_API_VERSIONS


def is_kind_allowed(key: tuple[str, str]) -> bool:
    """Validate the resource is allowed."""
    return key in ALLOWED_API_RESOURCES or key[1] in ALLOWED_API_VERSIONS


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


def validate_ingress(ingress: dict[str, Any]) -> bool:
    """Validate that the ingress is valid."""
    keys = ingress["metadata"].get("annotations", {}).keys()
    return all([key for key in keys if key not in ALLOWED_INGRESS_ANNOTATIONS])


VALIDATION_HOOKS: dict[Callable[[dict[str, Any]], None]] = {
    "Ingress": [validate_ingress]
}


async def validate_resources(resources: dict[str, Any]) -> bool:
    """Test method that asserts that resources are valid."""
    k8s_resources = [
        resource for resource in resources if resource is not None and is_k8s(resource)
    ]

    # Must have at least one valid resource
    if not any(k8s_resources):
        _LOGGER.error("Did not have at least one valid resource")
        return False

    kinds = set(map(kind, k8s_resources))

    not_found = [kind for kind in kinds if not is_kind_allowed(kind)]
    if not_found:
        _LOGGER.error("Resource version not in allow list: %s", not_found)
        return False

    for k8s_resource in k8s_resources:
        key = kind(k8s_resource)[0]
        for hook in VALIDATION_HOOKS.get(key, []):
            if not hook(k8s_resource):
                _LOGGER.debug("Valid hook for %s", key)
                return False

    return True
