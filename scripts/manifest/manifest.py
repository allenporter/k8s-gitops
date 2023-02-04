"""Library for working with the manifest."""

import datetime
from dataclasses import dataclass
from functools import cache
import os
from pathlib import Path
from typing import Any
import yaml

from pydantic import BaseModel
import git


MANIFEST_FILE = Path("clusters/manifest.yaml")


@cache
def repo_root() -> Path:
    git_repo = git.Repo(os.getcwd(), search_parent_directories=True)
    return Path(git_repo.git.rev_parse("--show-toplevel"))


@dataclass
class HelmRelease:
    """A HelmRelease denormalized into the manifest."""

    name: str
    namespace: str
    repo_name: str
    repo_namespace: str

    @classmethod
    def from_doc(cls, doc: dict[str, Any]) -> "HelmRelease":
        """Parse a HelmRelease from a kubernetes resource."""
        if not (metadata := doc.get("metadata")):
            raise ValueError(f"Invalid {cls} missing metdata: {doc}")
        if not (name := metadata.get("name")):
            raise ValueError(f"Invalid {cls} missing metadata.name: {doc}")
        if not (namespace := metadata.get("namespace")):
            raise ValueError(f"Invalid {cls} missing metadata.namespace: {doc}")
        if not (spec := doc.get("spec")):
            raise ValueError(f"Invalid {cls} missing spec: {doc}")
        if not (chart := spec.get("chart")):
            raise ValueError(f"Invalid {cls} missing spec.chart: {doc}")
        if not (chart_spec := chart.get("spec")):
            raise ValueError(f"Invalid {cls} missing spec.chart.spec: {doc}")
        if not (source_ref := chart_spec.get("sourceRef")):
            raise ValueError(f"Invalid {cls} missing spec.chart.spec.sourceRef: {doc}")
        if "namespace" not in source_ref or "name" not in source_ref:
            raise ValueError(f"Invalid {cls} missing sourceRef fields: {doc}")
        return cls(name, namespace, source_ref["name"], source_ref["namespace"])

    @property
    def id(self) -> str:
        """Identifier for the HelmRelease in tests."""
        return f"{self.namespace}-{self.name}"


@dataclass
class HelmRepository:
    """A HelmRepository denormalized into the manifest."""

    name: str
    namespace: str
    url: str

    @classmethod
    def from_doc(cls, doc: dict[str, Any]) -> "HelmRepostory":
        """Parse a HelmRepository from a kubernetes resource."""
        if not (metadata := doc.get("metadata")):
            raise ValueError(f"Invalid {cls} missing metdata: {doc}")
        if not (name := metadata.get("name")):
            raise ValueError(f"Invalid {cls} missing metadata.name: {doc}")
        if not (namespace := metadata.get("namespace")):
            raise ValueError(f"Invalid {cls} missing metadata.namespace: {doc}")
        if not (spec := doc.get("spec")):
            raise ValueError(f"Invalid {cls} missing spec: {doc}")
        if not (url := spec.get("url")):
            raise ValueError(f"Invalid {cls} missing spec.url: {doc}")
        return cls(name, namespace, url)

    @property
    def id(self) -> str:
        """Identifier for the HelmRepository in tests."""
        return f"{self.namespace}-{self.name}"


@dataclass
class Kustomization:
    """A Kustomization is a set of declared cluster artifacts."""

    name: str
    path: str
    helm_repos: list[HelmRepository]
    helm_releases: list[HelmRelease]

    @property
    def full_path(self) -> Path:
        """Return the full cluster path for this object."""
        return repo_root() / self.path

    @property
    def id(self) -> str:
        """Identifier for the Kustomization in tests"""
        return f"{self.path}"


@dataclass
class Cluster:
    """A set of nodes that run containerized applications."""

    name: str
    path: str
    kustomizations: list[Kustomization]

    def helm_repo_config(self) -> dict[str, Any]:
        """Return a synthetic HelmRepoistory config."""
        now = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)
        repos = []
        for kustomize in self.kustomizations:
            repos.extend(
                [
                    {
                        "name": f"{repo.namespace}-{repo.name}",
                        "url": repo.url,
                    }
                    for repo in kustomize.helm_repos
                ]
            )
        return {
            "apiVersion": "",
            "generated": now.isoformat(),
            "repositories": repos,
        }

    @property
    def id(self) -> str:
        """Identifier for the Cluster in tests."""
        return f"{self.path}"


class Manifest(BaseModel):
    """Holds information about cluster and applications."""

    clusters: list[Cluster]


def manifest_file() -> Path:
    """Return the path to the manifest file."""
    root = repo_root()
    return Path(root) / MANIFEST_FILE


def manifest() -> Manifest:
    """Return the contents of the manifest file."""
    contents = manifest_file().read_text()
    doc = next(yaml.load_all(contents, Loader=yaml.Loader))
    if "spec" not in doc:
        raise ValueError("Manifest file malformed, missing 'spec'")
    return Manifest(clusters=doc["spec"])
