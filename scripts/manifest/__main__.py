"""Validate manifests."""

from __future__ import annotations

import pytest
import datetime
import git
import os
import sys
import subprocess
from pathlib import Path
import subprocess
import logging
import yaml
from functools import cache
from typing import Generator, Any


_LOGGER = logging.getLogger(__name__)


MANIFEST_FILE = Path("clusters/manifest.yaml")

KUSTOMIZE_KIND = "Kustomization"
KUSTOMIZE_API_VERSION = "kustomize.toolkit.fluxcd.io/v1beta2"
KUSTOMIZE_NAME = "flux-system"

KUSTOMIZE_BIN = "kustomize"

HELMREPO_KINDS = {("HelmRepository", "source.toolkit.fluxcd.io/v1beta2")}
HELMRELEASE_KINDS = {("HelmRelease", "helm.toolkit.fluxcd.io/v2beta1")}


def repo_root() -> Path:
    git_repo = git.Repo(os.getcwd(), search_parent_directories=True)
    return Path(git_repo.git.rev_parse("--show-toplevel"))


def get_kustomizations(root: Path) -> Generator[dict[str, Any], None, None]:
    """Return the Kustomization environments found in the cluster."""
    cmd = [KUSTOMIZE_BIN, "cfg", "grep", f"kind={KUSTOMIZE_KIND}", str(root)]
    p1 = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    cmd2 = [
        KUSTOMIZE_BIN,
        "cfg",
        "grep",
        f"metadata.name={KUSTOMIZE_NAME}",
        "--invert-match",
    ]
    p2 = subprocess.Popen(cmd2, stdin=p1.stdout, stdout=subprocess.PIPE)
    p1.stdout.close()  # Allow p1 to receive a SIGPIPE if p2 exits.
    (out, err) = p2.communicate()
    if p2.returncode:
        _LOGGER.error("Subprocess failed with return code %s", p2.returncode)
        if out:
            _LOGGER.info(out.decode("utf-8"))
        if err:
            _LOGGER.error(err.decode("utf-8"))
        raise ValueError(f"Subprocess failed with return code: {p2.returncode}")

    for doc in yaml.safe_load_all(out.decode("utf-8")):
        yield doc


def get_cluster_docs(root: Path) -> Generator[dict[str, Any], None, None]:
    """Return the Kustomization environments found in the cluster."""
    cmd = [KUSTOMIZE_BIN, "cfg", "grep", f"kind={KUSTOMIZE_KIND}", str(root)]
    p1 = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    cmd2 = [KUSTOMIZE_BIN, "cfg", "grep", f"metadata.name={KUSTOMIZE_NAME}"]
    p2 = subprocess.Popen(cmd2, stdin=p1.stdout, stdout=subprocess.PIPE)
    p1.stdout.close()  # Allow p1 to receive a SIGPIPE if p2 exits.
    (out, err) = p2.communicate()
    if p2.returncode:
        if out:
            _LOGGER.info(out.decode("utf-8"))
        if err:
            _LOGGER.error(err.decode("utf-8"))
        raise ValueError(f"Subprocess failed with return code: {p2.returncode}")

    for doc in yaml.safe_load_all(out.decode("utf-8")):
        yield doc


def main() -> int:
    """Validate manifests."""
    root = repo_root()
    manifest_file = Path(root) / MANIFEST_FILE

    clusters = []
    for cluster in get_cluster_docs(root):
        if "metadata" not in cluster or "name" not in cluster["metadata"]:
            raise ValueError(f"Invalid Kustomization did not have metadata.name")
        if "spec" not in cluster or "path" not in cluster["spec"]:
            raise ValueError(f"Invalid Kustomization did not have spec.path: {doc}")
        name = cluster["metadata"]["name"]
        path = cluster["spec"]["path"]

        cluster_root = Path(root) / path.lstrip("./")

        kustomizations = []
        for kustomization in get_kustomizations(cluster_root):
            annotations = kustomization["metadata"].get("annotations", {})
            if (
                orig_path := annotations.get("internal.config.kubernetes.io/path")
            ) and orig_path.startswith(KUSTOMIZE_NAME):
                continue

            if (
                "metadata" not in kustomization
                or "name" not in kustomization["metadata"]
            ):
                raise ValueError(
                    f"Invalid Kustomization did not have metadata.name: {kustomization}"
                )
            if "spec" not in kustomization or "path" not in kustomization["spec"]:
                raise ValueError(
                    f"Invalid Kustomization did not have spec.path: {kustomization}"
                )
            kustomization_name = kustomization["metadata"]["name"]
            kustomization_path = kustomization["spec"]["path"]
            assert kustomization_name in kustomization_path
            kustomizations.append(
                {
                    "name": kustomization_name,
                    "path": kustomization_path,
                }
            )

        clusters.append({"name": name, "path": path, "kustomizations": kustomizations})

    content = yaml.dump({"spec": clusters})

    if manifest_file.read_text() == content:
        return

    manifest_file.write_text(content)


if __name__ == "__main__":
    sys.exit(main())
