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

from scripts.manifest import manifest

from .conftest import (
    kustomize_build_resources,
    kind,
    is_kind_allowed,
    validate_resources,
)

_LOGGER = logging.getLogger(__name__)


KUSTOMIZATIONS = [
    kustomization
    for cluster in manifest.manifest().clusters
    for kustomization in cluster.kustomizations
]


@pytest.fixture(
    name="kustomize_file",
    params=[kustomization.full_path for kustomization in KUSTOMIZATIONS],
    ids=(kustomization.path for kustomization in KUSTOMIZATIONS),
)
def kustomize_files_fixture(request: Any) -> Generator[str, None, None]:
    """Fixture that produces yaml document contents."""
    return request.param


@pytest.fixture(name="resources")
async def kustomize_build_fixture(kustomize_file: str) -> list[dict[str, Any]]:
    """Fixture that runs kustomize build on kustomize inptus."""
    return await kustomize_build_resources(kustomize_file)


async def test_allowed_resource(resources: list[dict[str, Any]]) -> None:
    """Validate the resource."""
    assert await validate_resources(resources), f"Invalid resources: {resources}"
