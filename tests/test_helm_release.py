"""Validates that all files in the repo are valid kustomizations."""

from __future__ import annotations

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
    kustomize_build_resources,
    kind_filter,
    kind,
    is_kind_allowed,
    HELMRELEASE_KINDS,
    validate_resources,
)

_LOGGER = logging.getLogger(__name__)


MANIFEST = manifest.manifest()
KUSTOMIZATION_PARAMS = [
    (cluster, kustomization)
    for cluster in MANIFEST.clusters
    for kustomization in cluster.kustomizations
    if kustomization.helm_releases
]

HELM_REPOS = {cluster.path: cluster.helm_repo_config() for cluster in MANIFEST.clusters}


@pytest.fixture(name="tmp_config_path", scope="module")
def tmp_config_path_fixture(tmp_path_factory: Any) -> Generator[Path, None, None]:
    """Fixture for creating a path used for helm config shared across tests."""
    yield tmp_path_factory.mktemp("helm")


@pytest.fixture(name="helm_raw_command", scope="module")
def helm_raw_command_fixture(tmp_config_path: Path) -> Callable[[...], Any]:
    """Fixture that produces a helm command."""
    cache_dir = tmp_config_path / "cache"

    def run(args: list[str]) -> None:
        return cmd.run_command(
            [
                "helm",
                *args,
                "--registry-config",
                "/dev/null",
                "--repository-cache",
                str(cache_dir),
            ]
        )

    return run


@pytest.fixture(autouse=True, scope="module")
def helm_update_repo_cache_fixture(
    tmp_config_path: Path, helm_raw_command: Callable[[...], Any]
) -> None:
    """Fixture to update the helm repository for all environments."""

    for cluster in MANIFEST.clusters:
        repo_config_file = tmp_config_path / f"{slugify(cluster.path)}-repo-config.yaml"
        repo_config_file.write_text(yaml.dump(HELM_REPOS[cluster.path]))
        assert helm_raw_command(
            ["repo", "update", "--repository-config", repo_config_file]
        )


@pytest.fixture(
    name="test_config",
    params=[(k[0].path, k[1].full_path) for k in KUSTOMIZATION_PARAMS],
    ids=[f"{k[0].path}-{k[1].path}" for k in KUSTOMIZATION_PARAMS],
)
def test_config_fixture(request: Any) -> tuple[str, str] | None:
    """Fixture that produces yaml document contents."""
    return request.param


@pytest.fixture(name="cluster_path")
def env_fixture(test_config: tuple[str, str]) -> str:
    """Fixture returns the current k8s environment under test."""
    return test_config[0]


@pytest.fixture(name="kustomization_file")
def kustomization_file_fixture(test_config: tuple[str, str] | None) -> str | None:
    """Fixture that produces the current kustomization file."""
    return test_config[1]


@pytest.fixture(name="helm_command")
def helm_command_fixture(
    tmp_config_path: Path, cluster_path: str, helm_raw_command: Callable[[...], Any]
) -> Callable[[...], Any]:
    """Fixture that produces a helm command."""
    repo_config_file = tmp_config_path / f"{slugify(cluster_path)}-repo-config.yaml"

    def run(args: list[str]) -> None:
        return helm_raw_command([*args, "--repository-config", repo_config_file])

    return run


@pytest.fixture(name="resources")
def kustomize_build_fixture(kustomization_file: str) -> list[dict[str, Any]] | None:
    """Fixture that runs kustomize build on kustomize inptus."""
    return kustomize_build_resources(kustomization_file)


@pytest.fixture(name="helm_releases")
def helm_releases_fixture(resources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Fixture to produce HelmReleases in the module."""
    # TODO: Replace with kustomize grep and pipe
    return list(filter(kind_filter(HELMRELEASE_KINDS), resources))


def test_validate_helm_release(
    helm_releases: list[dict[str, Any]],
    helm_command: Callable[[...], Any],
    tmp_config_path: Path,
):
    """Validate helm releases"""

    for helm_release in helm_releases:
        assert "metadata" in helm_release
        name = helm_release["metadata"].get("name")

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

        args = [
            "template",
            name,
            f"{repo}/{chart_spec['chart']}",
            "--debug",
            "--version",
            chart_spec["version"],
        ]
        values = helm_release["spec"].get("values")
        if values:
            values_yaml = tmp_config_path / "values.yaml"
            values_yaml.write_text(yaml.dump(values))
            args.extend(["--values", str(values_yaml)])
        out = helm_command(args)
        assert validate_resources(
            yaml.safe_load_all(out)
        ), f"Invalid HelmRelease: {helm_release}"
