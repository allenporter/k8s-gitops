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

from scripts.manifest import manifest, cmd

from .conftest import POLICY_DIR

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


async def test_validate_policies(kustomize_file: Path) -> None:
    """Validate resources against kyverno policies."""
    await cmd.run_piped_commands(
        [
            ["kustomize", "build", str(kustomize_file)],
            # Exclude secrets which kyverno may have a problem handling
            ["kustomize", "cfg", "grep", "--invert-match", "kind=Secret"],
            [
                "kyverno",
                "apply",
                POLICY_DIR,
                "--resource",
                "-",
            ],
        ]
    )
