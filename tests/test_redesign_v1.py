"""Redesign v1 adherence tests."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import validate_redesign_v1 as v  # noqa: E402


def test_validate_redesign_v1_exits_zero():
    proc = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "validate_redesign_v1.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stdout + "\n" + proc.stderr


@pytest.fixture(scope="module")
def forest_nesting_findings():
    data = v.load_yaml()
    concepts = v.by_id(data)
    pm = v.parents_map(data)
    findings: list[v.Finding] = []
    v.check_forest_nesting(findings, concepts, pm)
    return findings


def _fail_msg(findings: list[v.Finding], check_id: str) -> str:
    bad = [f for f in findings if f.check_id == check_id]
    if not bad:
        return ""
    return "\n".join(str(f) for f in bad)


def test_forest_patterns_nest_under_rules(forest_nesting_findings):
    """Every Forest pattern chemist home nests under its rule chemist home."""
    msg = _fail_msg(forest_nesting_findings, "forest_pattern_under_rule")
    assert not msg, msg


def test_forest_rules_nest_under_rulesets(forest_nesting_findings):
    """Every rule with ruleset membership nests under that ruleset home."""
    msg = _fail_msg(forest_nesting_findings, "forest_rule_under_ruleset")
    assert not msg, msg


def test_forest_rulesets_nest_under_parents(forest_nesting_findings):
    """SO/UO/DH⊂oxidation, HD⊂isoredox, RD/CJ⊂reaction class, PhaseOne⊂disposition."""
    msg = _fail_msg(forest_nesting_findings, "forest_ruleset_nesting")
    assert not msg, msg


@pytest.fixture(scope="module")
def dealk_always_with_findings():
    data = v.load_yaml()
    concepts = v.by_id(data)
    pm = v.parents_map(data)
    findings: list[v.Finding] = []
    v.check_dealkylation_pattern_always_with(findings, concepts, pm)
    return findings


def test_dealkylation_patterns_have_always_with(dealk_always_with_findings):
    """Each Dealkylation/NDealkylation pattern mapping carries always_with descriptors."""
    msg = _fail_msg(dealk_always_with_findings, "dealk_always_with")
    assert not msg, msg


def test_dealkylation_shared_homes_always_with_distinct(dealk_always_with_findings):
    """Patterns sharing one dealk site home differ in always_with sets."""
    msg = _fail_msg(dealk_always_with_findings, "dealk_always_with_distinct")
    assert not msg, msg


def test_ndealkylation_patterns_have_always_with(dealk_always_with_findings):
    """N-dealk subset covered by the shared dealk always_with policy."""
    msg = _fail_msg(dealk_always_with_findings, "dealk_always_with")
    assert not msg, msg


def test_ndealkylation_shared_homes_always_with_distinct(dealk_always_with_findings):
    msg = _fail_msg(dealk_always_with_findings, "dealk_always_with_distinct")
    assert not msg, msg


def test_ndealkylation_methyl_patterns_share_demethylation_home():
    """Regression: three methyl_* patterns share N-demethylation, distinguished by always_with."""
    rows = [
        r
        for r in v.load_sssom(v.FOREST_SSSOM)
        if (r.get("object_id") or "").startswith("forest.pattern:NDealkylation/methyl_")
    ]
    assert len(rows) == 3
    homes = {r["subject_id"] for r in rows}
    assert homes == {"xmet:3001200"}
    aw_sets = {
        frozenset(x for x in (r.get("always_with") or "").split("|") if x) for r in rows
    }
    assert len(aw_sets) == 3


def test_dealkylation_methyl_patterns_share_demethylation_home():
    """Regression: Dealkylation methyl_* share demethylation, distinguished by always_with."""
    rows = [
        r
        for r in v.load_sssom(v.FOREST_SSSOM)
        if (r.get("object_id") or "").startswith("forest.pattern:Dealkylation/methyl_")
    ]
    assert len(rows) == 3
    homes = {r["subject_id"] for r in rows}
    assert homes == {"xmet:3001194"}
    aw_sets = {
        frozenset(x for x in (r.get("always_with") or "").split("|") if x) for r in rows
    }
    assert len(aw_sets) == 3
