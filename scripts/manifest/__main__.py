"""Validate manifests."""

from __future__ import annotations

import asyncio
import pytest
import datetime
import dataclasses
import os
import sys
import subprocess
from pathlib import Path
import subprocess
import logging
import yaml
from functools import cache
from typing import Generator, Any

from flux_local import repo
from flux_local import kustomize
from flux_local.manifest import update_manifest


_LOGGER = logging.getLogger(__name__)


MANIFEST_FILE = Path("clusters/manifest.yaml")


async def main() -> int:
    """Validate manifests."""
    logging.basicConfig(level=logging.DEBUG)
    manifest = await repo.build_manifest()
    await update_manifest(MANIFEST_FILE, manifest)


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
