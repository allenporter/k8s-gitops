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

from flux_local import manifest, repo
from flux_local import kustomize


_LOGGER = logging.getLogger(__name__)


MANIFEST_FILE = Path("clusters/manifest.yaml")

KUSTOMIZE_BIN = "kustomize"

CLUSTER_KUSTOMIZE_KIND = "Kustomization"
CLUSTER_KUSTOMIZE_VERSIONS = {"kustomize.toolkit.fluxcd.io/v1beta2"}
# Flux cluster kustomizations
CLUSTER_KUSTOMIZE_NAME = "flux-system"

KUSTOMIZE_KIND = "Kustomization"
KUSTOMIZE_VERSIONS = {"kustomize.toolkit.fluxcd.io/v1beta2"}

HELM_REPO_KIND = "HelmRepository"
HELM_REPO_VERSIONS = {"source.toolkit.fluxcd.io/v1beta2"}

HELM_RELEASE_KIND = "HelmRelease"
HELM_RELEASE_VERSIONS = {"helm.toolkit.fluxcd.io/v2beta1"}


def kind_filter(kinds: set[tuple[str, str]]):
    """Return a yaml doc filter for specified resource type."""

    def func(doc):
        return doc.get("kind") in kinds

    return func


def version_filter(versions: set[tuple[str, str]]):
    """Return a yaml doc filter for specified resource version."""

    def func(doc):
        return doc.get("apiVersion") in versions

    return func


async def get_cluster_docs(root: Path) -> Generator[dict[str, Any], None, None]:
    """Return the Kustomization environments for flux clusters."""
    cmd = kustomize.grep(f"kind={CLUSTER_KUSTOMIZE_KIND}", root).grep(
        f"metadata.name={CLUSTER_KUSTOMIZE_NAME}"
    )
    objects = await cmd.objects()
    for doc in filter(version_filter(CLUSTER_KUSTOMIZE_VERSIONS), objects):
        yield doc


async def get_kustomizations(root: Path) -> Generator[dict[str, Any], None, None]:
    """Return the Kustomization environments found in the cluster."""
    cmd = kustomize.grep(f"kind={KUSTOMIZE_KIND}", root).grep(
        f"metadata.name={CLUSTER_KUSTOMIZE_NAME}", invert=True
    )
    objects = await cmd.objects()
    for doc in filter(version_filter(KUSTOMIZE_VERSIONS), objects):
        yield doc


async def get_helm_docs(root: Path) -> Generator[dict[str, Any], None, None]:
    """Return an HelmRepository objects in the cluster."""
    cmd = kustomize.build(root).grep(f"kind=({HELM_REPO_KIND}|{HELM_RELEASE_KIND})")
    objects = await cmd.objects()
    for doc in filter(
        version_filter(HELM_REPO_VERSIONS | HELM_RELEASE_VERSIONS),
        objects,
    ):
        yield doc


def manifest_file() -> Path:
    """Return the path to the manifest file."""
    root = repo.repo_root()
    return Path(root) / MANIFEST_FILE


def build_manifest() -> Manifest:
    """Return the contents of the manifest file."""
    contents = manifest_file().read_text()
    doc = next(yaml.load_all(contents, Loader=yaml.Loader))
    if "spec" not in doc:
        raise ValueError("Manifest file malformed, missing 'spec'")
    return Manifest(clusters=doc["spec"])


async def main() -> int:
    """Validate manifests."""
    logging.basicConfig(level=logging.DEBUG)
    root = repo.repo_root()
    print("Processing repo:", repo.repo_root())
    clusters = []
    async for cluster in get_cluster_docs(root):
        cluster_doc = manifest.Cluster.from_doc(cluster)
        cluster_root = root / cluster_doc.path.lstrip("./")
        print("Processing cluster", cluster_root)

        kustomizations = []
        async for kustomization in get_kustomizations(cluster_root):
            annotations = kustomization["metadata"].get("annotations", {})
            if (
                orig_path := annotations.get("internal.config.kubernetes.io/path")
            ) and orig_path.startswith(CLUSTER_KUSTOMIZE_NAME):
                continue
            doc = manifest.Kustomization.from_doc(kustomization)
            print("Processing Kustomization", doc.path)
            helm_docs = list([doc async for doc in get_helm_docs(doc.path)])
            doc.helm_repos = [
                manifest.HelmRepository.from_doc(doc)
                for doc in filter(kind_filter({HELM_REPO_KIND}), helm_docs)
            ]
            doc.helm_releases = [
                manifest.HelmRelease.from_doc(doc)
                for doc in filter(kind_filter({HELM_RELEASE_KIND}), helm_docs)
            ]
            cluster_doc.kustomizations.append(doc)

        clusters.append(cluster_doc)

    await manifest.update_manifest(
        manifest_file(), manifest.Manifest(clusters=clusters)
    )


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
