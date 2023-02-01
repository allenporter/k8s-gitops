"""Validates that all files in the repo are valid kustomizations."""

from __future__ import annotations

import aiofiles
import asyncio
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

KUSTOMIZE_BIN = "kustomize"
HELM_RELEASE_KIND = "HelmRelease"
HELM_RELEASE_VERSIONS = {"helm.toolkit.fluxcd.io/v2beta1"}


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
def helm_raw_command_fixture(tmp_config_path: Path) -> Callable[[...], Awaitable[Any]]:
    """Fixture that produces a helm command."""
    cache_dir = tmp_config_path / "cache"

    async def run(args: list[str]) -> None:
        return await cmd.run_command(
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
async def helm_update_repo_cache_fixture(
    tmp_config_path: Path, helm_raw_command: Callable[[...], Awaitable[Any]]
) -> None:
    """Fixture to update the helm repository for all environments."""

    for cluster in MANIFEST.clusters:
        repo_config_file = tmp_config_path / f"{slugify(cluster.path)}-repo-config.yaml"
        content = yaml.dump(HELM_REPOS[cluster.path])
        await asyncio.to_thread(repo_config_file.write_text, content)
        assert await helm_raw_command(
            ["repo", "update", "--repository-config", str(repo_config_file)]
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
def cluster_path_fixture(test_config: tuple[str, str]) -> str:
    """Fixture returns the current k8s environment under test."""
    return test_config[0]


@pytest.fixture(name="kustomization_file")
def kustomization_file_fixture(test_config: tuple[str, Path] | None) -> Path:
    """Fixture that produces the current kustomization file."""
    return test_config[1]


@pytest.fixture(name="helm_command")
def helm_command_fixture(
    tmp_config_path: Path,
    cluster_path: str,
    helm_raw_command: Callable[[...], Awaitable[Any]],
) -> Callable[[...], Any]:
    """Fixture that produces a helm command."""
    repo_config_file = tmp_config_path / f"{slugify(cluster_path)}-repo-config.yaml"

    async def run(args: list[str]) -> None:
        return await helm_raw_command(
            [*args, "--repository-config", str(repo_config_file)]
        )

    return run


@pytest.fixture(name="helm_releases")
async def get_helm_docs(kustomization_file: Path) -> list[dict[str, Any]]:
    """Return an HelmRelease objects in the cluster."""
    out = await cmd.run_piped_commands(
        [
            [KUSTOMIZE_BIN, "build", str(kustomization_file)],
            [
                KUSTOMIZE_BIN,
                "cfg",
                "grep",
                f"kind={HELM_RELEASE_KIND}",
            ],
        ]
    )
    return list(yaml.safe_load_all(out))


async def test_validate_helm_release(
    helm_releases: list[dict[str, Any]],
    helm_command: Callable[[...], Awaitable[Any]],
    tmp_config_path: Path,
):
    """Validate helm releases"""
    cmds = []
    for helm_release in helm_releases:
        metadata = helm_release["metadata"]
        assert "metadata" in helm_release
        name = f"{metadata['namespace']}-{metadata['name']}"

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
            values_file = (
                tmp_config_path / f"{slugify(name)}-{slugify(repo)}-values.yaml"
            )
            async with aiofiles.open(values_file, mode="w") as f:
                await f.write(yaml.dump(values))
            args.extend(["--values", str(values_file)])
        cmds.append(args)

    tasks = []
    for cmd in cmds:
        tasks.append(helm_command(cmd))

    results = await asyncio.gather(*tasks)
    for result in results:
        assert validate_resources(yaml.safe_load_all(result)), f"Invalid HelmRelease"
