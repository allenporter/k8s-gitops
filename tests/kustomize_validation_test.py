"""Validates that all files in the repo are valid kustomizations."""

import pytest
import git
import os
import subprocess
import logging

_LOGGER = logging.getLogger(__name__)

KUSTOMIZE_CONFIG = "kustomization.yaml"
KUSTOMIZE_FLAGS = ["--allow-id-changes=false"]


def kustomize_build(filename):
    command = ["kustomize", "build", filename]
    command.extend(KUSTOMIZE_FLAGS)
    proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (out, err) = proc.communicate()
    if proc.returncode:
        _LOGGER.error(
            "Subprocess failed %s with return code %s", command, proc.returncode
        )
        _LOGGER.info(out.decode("utf-8"))
        _LOGGER.error(err.decode("utf-8"))
        return None
    return out.decode("utf-8")


def repo_root():
    git_repo = git.Repo(os.getcwd(), search_parent_directories=True)
    return git_repo.git.rev_parse("--show-toplevel")


def kustomization_files():
    root = repo_root()
    matches = []
    for dirname, dirs, files in os.walk(root):
        basedirname = dirname[len(root) + 1 :]
        for filename in files:
            if filename != KUSTOMIZE_CONFIG:
                continue
            matches.append(basedirname)
    return matches


@pytest.mark.parametrize("filename", kustomization_files())
def test_validate_kustomization_file(filename):
    root = repo_root()
    full_path = f"{root}/{filename}"
    assert kustomize_build(full_path)
