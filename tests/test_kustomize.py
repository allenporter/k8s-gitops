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
    repo_root,
    kustomization_files,
    run_command,
    kustomize_build_resources,
    kind,
    is_k8s,
    is_kind_allowed,
    validate_resources,
)

_LOGGER = logging.getLogger(__name__)

EXCLUDE_FILES = {}


def test_kustomize_version():
    command = ["kustomize", "version"]
    _LOGGER.info(run_command(command))


@pytest.fixture(name="kustomize_file", params=kustomization_files(repo_root()))
def kustomize_files_fixture(request: Any, root: str) -> Generator[str, None, None]:
    """Fixture that produces yaml document contents."""
    if request.param in EXCLUDE_FILES:
        pytest.skip("File excluded from tests")
        return
    return f"{root}/{request.param}"


@pytest.fixture(name="resources")
def kustomize_build_fixture(kustomize_file: str) -> list[dict[str, Any]]:
    """Fixture that runs kustomize build on kustomize inptus."""
    return kustomize_build_resources(kustomize_file)


def test_allowed_resource(resources: list[dict[str, Any]]) -> None:
    """Validate the resource."""
    validate_resources(resources)
