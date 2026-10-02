"""Validate XMET and the repositories that depend on it against the XMET spec.

The same entry points back XMET's own test suite, the ``xmet-validate`` command,
and checks run from sibling repositories (Forest, tagger, …)::

    from xenosite.xmet.validate import validate_forest
    report = validate_forest("crates/xenosite-forest/src/rules.rs")
    assert report.ok, report.text()

Findings listed in ``data/mappings/validation-xfail.tsv`` are reported as
expected failures and do not fail a report.
"""

from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path

from xenosite.xmet.validate import core
from xenosite.xmet.validate.core import Finding
from xenosite.xmet.validate.curies import curie_findings
from xenosite.xmet.validate.forest import forest_findings
from xenosite.xmet.validate.tagger import tagger_findings

__all__ = [
    "Finding",
    "Report",
    "sources",
    "validate_curies",
    "validate_forest",
    "validate_ontology",
    "validate_tagger",
]


@dataclass
class Report:
    """Findings from one validation, split into hard failures and expected failures."""

    name: str
    failures: list[Finding] = field(default_factory=list)
    expected: list[Finding] = field(default_factory=list)

    @classmethod
    def from_findings(cls, name: str, findings: list[Finding]) -> Report:
        xfail = core.load_xfail()
        report = cls(name)
        for f in findings:
            if f.key() in xfail or (f.check_id, f.subject_id, "") in xfail:
                report.expected.append(f)
            else:
                report.failures.append(f)
        return report

    @property
    def ok(self) -> bool:
        return not self.failures

    def by_check(self) -> dict[str, list[Finding]]:
        groups: dict[str, list[Finding]] = defaultdict(list)
        for f in self.failures:
            groups[f.check_id].append(f)
        return dict(sorted(groups.items()))

    def text(self) -> str:
        n = len(self.failures) + len(self.expected)
        lines = [f"{self.name}: findings: {n}  hard: {len(self.failures)}  xfail: {len(self.expected)}"]
        lines += [f"XFAIL {f}" for f in self.expected]
        for check_id, group in self.by_check().items():
            lines.append(f"\n== {check_id} ({len(group)}) ==")
            lines += [f"FAIL  {f}" for f in group]
        return "\n".join(lines)

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "ok": self.ok,
            "failures": [f.to_dict() for f in self.failures],
            "expected": [f.to_dict() for f in self.expected],
        }

    def json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)


@contextmanager
def sources(
    forest_sssom: str | Path | None = None,
    tagger_sssom: str | Path | None = None,
    ontology_yaml: str | Path | None = None,
    remap: str | Path | None = None,
) -> Iterator[None]:
    """Temporarily validate candidate files in place of XMET's copies.

    A sibling repository uses this (or ``xmet-validate --forest-sssom …``) to check
    a regenerated mapping before proposing it; ``xmet-edit`` uses it to validate an
    ontology with a patch applied.
    """
    names = ("FOREST_SSSOM", "TAGGER_SSSOM", "YAML_PATH", "REMAP_PATH")
    saved = {n: getattr(core, n) for n in names}
    try:
        for name, value in zip(names, (forest_sssom, tagger_sssom, ontology_yaml, remap)):
            if value is not None:
                setattr(core, name, Path(value).resolve())
        yield
    finally:
        for name, value in saved.items():
            setattr(core, name, value)


def validate_ontology() -> Report:
    """Every in-repo spec check: hierarchy, relations, definitions, and SSSOM discipline."""
    return Report.from_findings("ontology", core.ontology_findings())


def validate_forest(rules_rs: str | Path) -> Report:
    """A Forest ``rules.rs`` against XMET's Forest SSSOM (coverage, orphans, nesting)."""
    return Report.from_findings("forest", forest_findings(Path(rules_rs)))


def validate_tagger(rules_dir: str | Path) -> Report:
    """A tagger rules directory against XMET's tagger SSSOM (coverage, orphans)."""
    return Report.from_findings("tagger", tagger_findings(Path(rules_dir)))


def validate_curies(paths: list[str | Path]) -> Report:
    """``xmet:`` CURIEs in files or directories are live concepts (names replacements for retired ids)."""
    return Report.from_findings("curies", curie_findings([Path(p) for p in paths]))
