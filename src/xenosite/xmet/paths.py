"""Locate XMET data files in this repository."""

from __future__ import annotations

from pathlib import Path


def repo_root() -> Path:
    # src/xenosite/xmet/paths.py → parents[3] = repo root
    return Path(__file__).resolve().parents[3]


def data_dir() -> Path:
    return repo_root() / "data"


def ontology_yaml() -> Path:
    return data_dir() / "ontology" / "xmet.yaml"
