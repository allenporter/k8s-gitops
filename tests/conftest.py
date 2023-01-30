"""Validates that all files in the repo are valid kustomizations."""

from __future__ import annotations

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

_LOGGER = logging.getLogger(__name__)


KUSTOMIZE_BIN = "kustomize"
KUSTOMIZE_CONFIG = "kustomization.yaml"
KUSTOMIZE_FLAGS = []

KUSTOMIZATION_KINDS = {
    ("Kustomization", "kustomize.toolkit.fluxcd.io/v1beta1"),
    ("Kustomization", "kustomize.toolkit.fluxcd.io/v1beta2"),
}
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

EXCLUDE_FILES = {}


def run_command(command: list[str], std_in: str | None = None) -> str:
    """Run the specified command and return stdout."""
    proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (out, err) = proc.communicate(input=std_in)
    if proc.returncode:
        _LOGGER.error(
            "Subprocess failed %s with return code %s", command, proc.returncode
        )
        _LOGGER.info(out.decode("utf-8"))
        _LOGGER.error(err.decode("utf-8"))
        return None
    return out.decode("utf-8")


def kustomize_grep(cluster_path: Path, kind: str):
    """Loads all Kustomizations for a specific kind as a yaml object."""
    command = [KUSTOMIZE_BIN, "cfg", "grep", f"kind={kind}", str(cluster_path)]
    doc_contents = run_command(command)
    assert doc_contents
    for doc in yaml.safe_load_all(doc_contents):
        yield doc


def kind_filter(kinds: set[tuple[str, str]]):
    """Return a yaml doc filter for specified resource type and version."""

    def func(doc):
        return (doc.get("kind"), doc.get("apiVersion")) in kinds

    return func


def kustomize_build(filename: str) -> str:
    """Return kustomize build and return the string contents."""
    command = ["kustomize", "build", filename]
    command.extend(KUSTOMIZE_FLAGS)
    return run_command(command)


@cache
def kustomize_build_resources(filename: str) -> list[dict[str, Any]]:
    """Run kustomize build and return the parsed objects."""
    doc_contents = kustomize_build(filename)
    return list(yaml.safe_load_all(doc_contents))


@cache
def repo_root() -> Path:
    git_repo = git.Repo(os.getcwd(), search_parent_directories=True)
    return Path(git_repo.git.rev_parse("--show-toplevel"))


@pytest.fixture(name="root", scope="session")
def repo_root_fixture() -> str:
    """Github repo root directory."""
    return repo_root()


@cache
def kustomization_files(root: Path) -> list[str]:
    """Return Kustomizations in the specified root."""
    matches = []
    yaml_docs = kustomize_grep(root, "Kustomization")
    for doc in filter(kind_filter(KUSTOMIZATION_KINDS), yaml_docs):
        if doc["metadata"]["name"] == "flux-system":
            continue
        if doc["spec"]["sourceRef"]["kind"] != "GitRepository":
            continue
        if "path" not in doc["spec"]:
            raise Exception(f"Invalid spec/path in doc {doc}")
        path = doc["spec"]["path"]
        matches.append(path.lstrip("./"))
    return matches


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
