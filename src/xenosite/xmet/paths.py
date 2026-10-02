"""Locate XMET data files.

In a source checkout (including a git submodule) data is read from the
repository. An installed wheel carries a copy of the same tree under
``xenosite/xmet/_data`` (see ``[tool.hatch.build.targets.wheel.force-include]``).
"""

from __future__ import annotations

from pathlib import Path

_PACKAGED = Path(__file__).resolve().parent / "_data"


def repo_root() -> Path:
    # src/xenosite/xmet/paths.py → parents[3] = repo root
    return Path(__file__).resolve().parents[3]


def resource_root() -> Path:
    """Directory holding ``data/`` and ``revision/``: the checkout, else the wheel copy."""
    root = repo_root()
    if (root / "data" / "ontology" / "xmet.yaml").is_file():
        return root
    return _PACKAGED


def data_dir() -> Path:
    return resource_root() / "data"


def ontology_yaml() -> Path:
    return data_dir() / "ontology" / "xmet.yaml"
