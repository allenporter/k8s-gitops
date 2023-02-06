"""Validates that all files in the repo are valid kustomizations."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path
import datetime
import git
import os
import subprocess
import logging
from typing import Generator, Any

import aiofiles
from aiofiles.os import mkdir
from flux_local import manifest, kustomize
from flux_local.helm import Helm
import pytest
from slugify import slugify
import yaml

from .conftest import (
    POLICY_DIR,
)

_LOGGER = logging.getLogger(__name__)

KUSTOMIZE_BIN = "kustomize"
HELM_RELEASE_KIND = "HelmRelease"
HELM_RELEASE_VERSIONS = {"helm.toolkit.fluxcd.io/v2beta1"}


MANIFEST = manifest.Manifest.parse_yaml(Path("clusters/manifest.yaml").read_text())


@dataclass
class Param:
    """Parameters to each test built from the cluster manifest."""

    cluster: manifest.Cluster
    kustomization: manifest.Kustomization
    helm_release: manifest.HelmRelease

    @property
    def id(self) -> str:
        """Identifer in tests."""
        return f"{self.cluster.id_name}-{self.kustomization.id_name}-{self.helm_release.release_name}"


TEST_PARAMS: list[Param] = [
    Param(cluster, kustomization, release)
    for cluster in MANIFEST.clusters
    for kustomization in cluster.kustomizations
    for release in kustomization.helm_releases
]


@pytest.fixture(name="tmp_config_path", scope="module")
def tmp_config_path_fixture(tmp_path_factory: Any) -> Generator[Path, None, None]:
    """Fixture for creating a path used for helm config shared across tests."""
    yield tmp_path_factory.mktemp("helm")


@pytest.fixture(name="helms", scope="module")
async def helms_fixture(tmp_config_path: Path) -> dict[str, Helm]:
    """Fixture that creates the Helm object and updates the repo."""
    cache_path = tmp_config_path / "cache"
    await mkdir(cache_path)

    helms: dict[str, Helm] = {}
    for cluster in MANIFEST.clusters:
        path = tmp_config_path / f"{slugify(cluster.path)}"
        await mkdir(path)
        helm = Helm(path, cache_path)
        for kustomization in cluster.kustomizations:
            for repo in kustomization.helm_repos:
                helm.add_repo(repo)
        await helm.update()
        helms[str(cluster.path)] = helm
    return helms


@pytest.fixture(
    name="test_config",
    params=TEST_PARAMS,
    ids=[param.id for param in TEST_PARAMS],
)
def test_config_fixture(request: Any) -> Param:
    """Fixture that produces the test configuration."""
    return request.param


@pytest.fixture(name="cluster")
def cluster_fixture(test_config: TestParam) -> manifest.Cluster:
    """Fixture returns the current k8s environment under test."""
    return test_config.cluster


@pytest.fixture(name="helm")
def helm_fixture(
    tmp_config_path: Path,
    helms: dict[str, Helm],
    cluster: manifest.Cluster,
) -> Helm:
    """Fixture that produces a helm command."""
    return helms[str(cluster.path)]


@pytest.fixture(name="helm_release")
async def load_helm_release(test_config: Param) -> dict[str, Any]:
    """Return an HelmRelease objects in the cluster."""
    cmd = (
        kustomize.build(str(test_config.kustomization.path))
        .grep(f"metadata.namespace=^{test_config.helm_release.namespace}$")
        .grep(f"metadata.name=^{test_config.helm_release.name}$")
        .grep(f"kind=^{HELM_RELEASE_KIND}$")
    )
    objects = await cmd.objects()
    assert len(objects) == 1
    return objects[0]


async def test_validate_helm_release(
    helm_release: dict[str, Any],
    helm: Helm,
    tmp_config_path: Path,
    test_config: Param,
):
    """Validate helm releases"""
    cmd = await helm.template(
        manifest.HelmRelease.from_doc(helm_release), helm_release["spec"].get("values")
    )
    await cmd.validate(POLICY_DIR)
