"""Validates that all files in the repo are valid kustomizations."""

from __future__ import annotations

import aiofiles
import asyncio
from dataclasses import dataclass
import pytest
import datetime
import git
import os
import subprocess
import logging
from slugify import slugify
from typing import Generator, Any
import yaml

from scripts.manifest import manifest, cmd

from .conftest import (
    POLICY_DIR,
)

_LOGGER = logging.getLogger(__name__)

KUSTOMIZE_BIN = "kustomize"
HELM_RELEASE_KIND = "HelmRelease"
HELM_RELEASE_VERSIONS = {"helm.toolkit.fluxcd.io/v2beta1"}


MANIFEST = manifest.manifest()


@dataclass
class Param:
    """Parameters to each test built from the cluster manifest."""

    cluster: manifest.Cluster
    kustomization: manifest.Kustomization
    helm_release: manifest.HelmRelease

    @property
    def id(self) -> str:
        """Identifer in tests."""
        return f"{self.cluster.id}-{self.kustomization.id}-{self.helm_release.id}"


TEST_PARAMS: list[Param] = [
    Param(cluster, kustomization, release)
    for cluster in MANIFEST.clusters
    for kustomization in cluster.kustomizations
    for release in kustomization.helm_releases
]

HELM_REPOS = {cluster.path: cluster.helm_repo_config() for cluster in MANIFEST.clusters}


@pytest.fixture(name="tmp_config_path", scope="module")
def tmp_config_path_fixture(tmp_path_factory: Any) -> Generator[Path, None, None]:
    """Fixture for creating a path used for helm config shared across tests."""
    yield tmp_path_factory.mktemp("helm")


@pytest.fixture(name="helm_raw_command", scope="module")
def helm_raw_command_fixture(tmp_config_path: Path) -> list[str]:
    """Fixture that produces a helm command."""
    cache_dir = tmp_config_path / "cache"
    return [
        "helm",
        "--registry-config",
        "/dev/null",
        "--repository-cache",
        str(cache_dir),
    ]


@pytest.fixture(autouse=True, scope="module")
async def helm_update_repo_cache_fixture(
    tmp_config_path: Path,
    helm_raw_command: list[str],
) -> None:
    """Fixture to update the helm repository for all environments."""

    for cluster in MANIFEST.clusters:
        repo_config_file = tmp_config_path / f"{slugify(cluster.path)}-repo-config.yaml"
        content = yaml.dump(HELM_REPOS[cluster.path])
        await asyncio.to_thread(repo_config_file.write_text, content)
        assert await cmd.run_command(
            helm_raw_command
            + ["repo", "update", "--repository-config", str(repo_config_file)]
        )


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


@pytest.fixture(name="helm_command")
def helm_command_fixture(
    tmp_config_path: Path,
    cluster: manifest.Cluster,
    helm_raw_command: list[str],
) -> list[str]:
    """Fixture that produces a helm command."""
    repo_config_file = tmp_config_path / f"{slugify(cluster.path)}-repo-config.yaml"
    return helm_raw_command + ["--repository-config", str(repo_config_file)]


@pytest.fixture(name="helm_release")
async def load_helm_release(test_config: Param) -> dict[str, Any]:
    """Return an HelmRelease objects in the cluster."""
    out = await cmd.run_piped_commands(
        [
            [KUSTOMIZE_BIN, "build", str(test_config.kustomization.path)],
            [
                KUSTOMIZE_BIN,
                "cfg",
                "grep",
                f"kind=^{HELM_RELEASE_KIND}$",
            ],
            [
                KUSTOMIZE_BIN,
                "cfg",
                "grep",
                f"metadata.namespace=^{test_config.helm_release.namespace}$",
            ],
            [
                KUSTOMIZE_BIN,
                "cfg",
                "grep",
                f"metadata.name=^{test_config.helm_release.name}$",
            ],
        ]
    )
    return yaml.safe_load(out)


async def test_validate_helm_release(
    helm_release: dict[str, Any],
    helm_command: list[str],
    tmp_config_path: Path,
    test_config: Param,
):
    """Validate helm releases"""
    assert helm_release

    metadata = helm_release["metadata"]
    assert "metadata" in helm_release
    name = f"{metadata['namespace']}-{metadata['name']}"
    assert test_config.helm_release.id == name

    assert "spec" in helm_release
    assert "chart" in helm_release["spec"]
    assert "spec" in helm_release["spec"]["chart"]

    chart_spec = helm_release["spec"]["chart"]["spec"]
    assert "chart" in chart_spec
    assert "version" in chart_spec, "Full data: %s" % (helm_release)
    assert "sourceRef" in chart_spec

    source_ref = chart_spec["sourceRef"]
    assert "name" in source_ref
    assert "namespace" in source_ref
    repo = "%s-%s" % (source_ref["namespace"], source_ref["name"])
    args = helm_command + [
        "template",
        name,
        f"{repo}/{chart_spec['chart']}",
        "--skip-crds",  # Reduce size of output
        "--debug",
        "--version",
        chart_spec["version"],
    ]
    values = helm_release["spec"].get("values")
    if values:
        values_file = tmp_config_path / f"{slugify(name)}-{slugify(repo)}-values.yaml"
        async with aiofiles.open(values_file, mode="w") as f:
            await f.write(yaml.dump(values))
        args.extend(["--values", str(values_file)])

    # Run helm template command and apply policies
    await cmd.run_piped_commands(
        [
            args,
            [
                "kyverno",
                "apply",
                POLICY_DIR,
                "--resource",
                "-",
            ],
        ]
    )
