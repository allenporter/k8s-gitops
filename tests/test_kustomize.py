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
from typing import Generator, Any

from flux_local import manifest, kustomize, repo

from .conftest import POLICY_DIR

_LOGGER = logging.getLogger(__name__)


MANIFEST = manifest.Manifest.parse_yaml(Path("clusters/manifest.yaml").read_text())

KUSTOMIZATIONS = [
    kustomization
    for cluster in MANIFEST.clusters
    for kustomization in cluster.kustomizations
]


@pytest.fixture(
    name="kustomize_file",
    params=[repo.repo_root() / kustomization.path for kustomization in KUSTOMIZATIONS],
    ids=(kustomization.path for kustomization in KUSTOMIZATIONS),
)
def kustomize_files_fixture(request: Any) -> Generator[str, None, None]:
    """Fixture that produces yaml document contents."""
    return request.param


async def test_validate_policies(kustomize_file: Path) -> None:
    """Validate resources against kyverno policies."""
    await kustomize.build(kustomize_file).validate(POLICY_DIR)
