"""Checks that ``xmet:`` CURIEs used in other repositories exist in the live ontology.

Retired, merged, and renumbered identifiers are resolved through
``xmet-id-remap.tsv`` and ``xmet-id-renumber.tsv`` so the finding names the
current replacement.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path

from xenosite.xmet.validate import core
from xenosite.xmet.validate.core import Finding

CURIE_RE = re.compile(r"\bxmet:(\d{7})\b")
TEXT_SUFFIXES = {".yaml", ".yml", ".json", ".jsonld", ".tsv", ".csv", ".ttl", ".md", ".txt", ".rs", ".py", ".toml"}


def load_successors() -> dict[str, str]:
    """old_id → new_id from the remap and renumber tables (first entry wins)."""
    out: dict[str, str] = {}
    for path in (core.REMAP_PATH, core.ROOT / "data/mappings/xmet-id-renumber.tsv"):
        if not path.exists():
            continue
        with path.open() as fh:
            for row in csv.DictReader(fh, delimiter="\t"):
                old, new = (row.get("old_id") or "").strip(), (row.get("new_id") or "").strip()
                if old and new and old != new:
                    out.setdefault(old, new)
    return out


def current_id(curie: str, live: set[str], successors: dict[str, str]) -> str | None:
    """Follow successor links from a retired id to a live one, if any."""
    seen = {curie}
    while curie not in live and curie in successors:
        curie = successors[curie]
        if curie in seen:
            return None
        seen.add(curie)
    return curie if curie in live else None


def iter_files(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for p in paths:
        if p.is_dir():
            files.extend(
                f for f in sorted(p.rglob("*"))
                if f.is_file() and f.suffix in TEXT_SUFFIXES and not any(part.startswith(".") for part in f.parts)
            )
        elif p.is_file():
            files.append(p)
    return files


def check_curies(findings: list[Finding], files: list[Path], live: set[str], successors: dict[str, str]) -> None:
    """Every ``xmet:`` CURIE in ``files`` is a live concept."""
    for f in files:
        try:
            text = f.read_text()
        except UnicodeDecodeError:
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            for m in CURIE_RE.finditer(line):
                curie = m.group(0)
                if curie in live:
                    continue
                repl = current_id(curie, live, successors)
                where = f"{f}:{lineno}"
                if repl:
                    findings.append(Finding("curie_retired", curie, f"retired id used at {where}; use {repl}", repl))
                else:
                    findings.append(Finding("curie_unknown", curie, f"unknown id used at {where}"))


def curie_findings(paths: list[Path]) -> list[Finding]:
    """Check ``xmet:`` CURIEs in the given files and directories."""
    live = set(core.by_id(core.load_yaml()))
    findings: list[Finding] = []
    check_curies(findings, iter_files(paths), live, load_successors())
    return findings
