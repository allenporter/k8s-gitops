"""Validates that all files in the repo are valid kustomizations."""

from __future__ import annotations

import pytest
import datetime
import git
import os
import subprocess
import logging
import yaml
from typing import Generator, Any

from .conftest import (
    kustomization_files,
    repo_root,
    kustomize_build_resources,
    kind_filter,
    HELMREPO_KINDS,
    run_command,
    is_k8s,
    kind,
    is_kind_allowed,
    HELMRELEASE_KINDS,
)

_LOGGER = logging.getLogger(__name__)


ENVS = ["prod", "dev"]

# Path that contains cluster Kustomations
KUSTOMIZATION_PATH_FORMAT = "clusters/{env}"

# Path to the Kustomization that contains cluster HelmRepository objects
HELMREPO_KUSTOMIZATION_PATH_FORMAT = "infrastructure/{env}"


KUSTOMIZATION_PARAMS = [
    (env, filename)
    for env in ENVS
    for filename in kustomization_files(
        repo_root() / KUSTOMIZATION_PATH_FORMAT.format(env=env)
    )
]


def helm_repos(env: str) -> list[dict[str, Any]]:
    """Build list of HelmReposity objects."""
    resources = kustomize_build_resources(
        HELMREPO_KUSTOMIZATION_PATH_FORMAT.format(env=env)
    )
    return list(filter(kind_filter(HELMREPO_KINDS), resources))


def helm_repo_config(helm_repos: list[dict[str, Any]]) -> dict[str, Any]:
    """Produce a helm repositor config."""
    return {
        "apiVersion": "",
        "generated": datetime.datetime.now(datetime.timezone.utc)
        .replace(microsecond=0)
        .isoformat(),
        "repositories": [
            {
                "name": "%s-%s"
                % (repo["metadata"]["namespace"], repo["metadata"]["name"]),
                "url": repo["spec"]["url"],
            }
            for repo in helm_repos
        ],
    }


HELM_REPOS = {env: helm_repo_config(helm_repos(env)) for env in ENVS}


@pytest.fixture(name="tmp_config_path", scope="module")
def tmp_config_path_fixture(tmp_path_factory: Any) -> Generator[Path, None, None]:
    """Fixture for creating a path used for helm config shared across tests."""
    yield tmp_path_factory.mktemp("helm")


@pytest.fixture(name="helm_raw_command", scope="module")
def helm_raw_command_fixture(tmp_config_path: Path,) -> Callable[[...], Any]:
    """Fixture that produces a helm command."""
    cache_dir = tmp_config_path / "cache"

    def run(args: list[str], stdin: str | None = None) -> None:
        return run_command(
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


def helm_repo_config_path(tmp_config_path: Path) -> Path:
    """Fixture with the file of the repo path."""
    return tmp_config_path / f"{env}-repo-config.yaml"


@pytest.fixture(autouse=True, scope="module")
def helm_update_repo_cache_fixture(
    tmp_config_path: Path, helm_raw_command: Callable[[...], Any]
) -> None:
    """Fixture to update the helm repository for all environments."""

    for env in ENVS:
        repo_config_file = tmp_config_path / f"{env}-repo-config.yaml"
        repo_config_file.write_text(yaml.dump(HELM_REPOS[env]))
        assert helm_raw_command(
            ["repo", "update", "--repository-config", repo_config_file]
        )


@pytest.fixture(
    name="test_config",
    params=KUSTOMIZATION_PARAMS,
    ids=[f"{k[0]}-{k[1]}" for k in KUSTOMIZATION_PARAMS],
)
def test_config_fixture(request: Any, root: str) -> tuple[str, str] | None:
    """Fixture that produces yaml document contents."""
    return (request.param[0], f"{root}/{request.param[1]}")


@pytest.fixture(name="env")
def env_fixture(test_config: tuple[str, str]) -> str:
    """Fixture returns the current k8s environment under test."""
    return test_config[0]


@pytest.fixture(name="helm_command")
def helm_command_fixture(
    tmp_config_path: Path, env: str, helm_raw_command: Callable[[...], Any]
) -> Callable[[...], Any]:
    """Fixture that produces a helm command."""
    repo_config_file = tmp_config_path / f"{env}-repo-config.yaml"

    def run(args: list[str], stdin: str | None = None) -> None:
        return helm_raw_command([*args, "--repository-config", repo_config_file])

    return run


@pytest.fixture(name="kustomization_file")
def kustomization_file_fixture(test_config: tuple[str, str] | None) -> str | None:
    """Fixture that produces the current kustomization file."""
    return test_config[1]


@pytest.fixture(name="resources")
def kustomize_build_fixture(kustomization_file: str) -> list[dict[str, Any]] | None:
    """Fixture that runs kustomize build on kustomize inptus."""
    return kustomize_build_resources(kustomization_file)


@pytest.fixture(name="helm_releases")
def helm_releases_fixture(resources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Fixture to produce HelmReleases in the module."""
    return list(filter(kind_filter(HELMRELEASE_KINDS), resources))


def test_validate_helm_release(
    helm_releases: list[dict[str, Any]], helm_command: Callable[[...], Any]
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

        values = helm_release["spec"].get("values", "")

        out = helm_command(
            [
                "template",
                name,
                f"{repo}/{chart_spec['chart']}",
                "--version",
                chart_spec["version"],
            ]
        )

        content = list(yaml.safe_load_all(out))
        k8s_resources = [
            resource
            for resource in content
            if resource is not None and is_k8s(resource)
        ]
        assert any(k8s_resources)

        kinds = set(map(kind, k8s_resources))
        not_found = [kind for kind in kinds if not is_kind_allowed(kind)]
        assert not not_found, "Resource version not in allow list"
