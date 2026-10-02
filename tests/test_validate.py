"""Sibling-repository validation API and ``xmet-validate`` CLI, on synthetic fixtures."""

from __future__ import annotations

import json
from pathlib import Path

from xenosite.xmet.validate import (
    core,
    sources,
    validate_curies,
    validate_forest,
    validate_ontology,
    validate_tagger,
)
from xenosite.xmet.validate.cli import main
from xenosite.xmet.validate.forest import RulesSource

RULES_RS = '''
/// Leaf with inline patterns.
pub fn hydroxylation() -> RuleSet {
    seal_leaf("Hydroxylation", RuleSet::new(Some("Hydroxylation".into()), [
        smirks_row("h", "[#6:1]>>[*:1]O", SiteKind::Atom, vec![1], Effect { ..Default::default() }),
        smirks_row("brand_new", "[#6:1]>>[*:1]O", SiteKind::Atom, vec![1], Effect { ..Default::default() }),
    ]))
}

static NOT_A_RULE: &[&str] = &["stray_literal"];

fn shared_patterns(flag: bool) -> Vec<PatternInfo> {
    vec![smirks_row("thiol", "[S:1]>>[*:1]", SiteKind::Atom, vec![1], Effect { ..Default::default() })]
}

fn wrapped_leaf(name: &'static str) -> RuleSet {
    seal_leaf(name, RuleSet::new(Some(name.into()), shared_patterns(true)))
}

/// Leaf built through a wrapper; patterns live in a helper.
pub fn gsh() -> RuleSet {
    wrapped_leaf_leaf("GSH")
}

fn wrapped_leaf_leaf(name: &'static str) -> RuleSet {
    wrapped_leaf(name)
}

pub fn reactivity() -> RuleSet {
    RuleSet::compose(Some("Reactivity".into()), [gsh()])
}
'''


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def ids(report) -> set[tuple[str, str]]:
    return {(f.check_id, f.object_id or f.subject_id) for f in report.failures}


# --- Forest -----------------------------------------------------------------------


def test_rules_source_follows_helpers_and_wrappers():
    src = RulesSource(RULES_RS)
    leaves = {name: src.patterns(fn) for fn, name in src.leaves.items()}
    assert leaves["Hydroxylation"] == ["h", "brand_new"]
    assert leaves["GSH"] == ["thiol"]
    assert "stray_literal" not in sum(leaves.values(), [])
    assert {src.catalogs[fn]: src.members(fn) for fn in src.catalogs} == {"Reactivity": ["GSH"]}


def test_forest_reports_unmapped_and_orphaned_patterns(tmp_path):
    report = validate_forest(write(tmp_path / "rules.rs", RULES_RS))
    found = ids(report)
    assert ("forest_pattern_coverage", "xf:Hydroxylation/brand_new") in found
    assert ("forest_pattern_coverage", "xf:Hydroxylation/h") not in found
    # Mapped in XMET but absent from this (tiny) catalog.
    assert ("forest_pattern_sssom_orphan", "xf:Hydroxylation/h2") in found
    assert not report.ok


# --- Tagger -----------------------------------------------------------------------


def test_tagger_reports_unmapped_and_orphaned_rules(tmp_path):
    mapped = next(r["object_id"] for r in core.load_sssom(core.TAGGER_SSSOM) if r["object_id"].startswith("rule:"))
    write(
        tmp_path / "rules" / "xenobiotic.rules.yaml",
        f"rules:\n  - id: {mapped}\n    reactant_smarts: '[#6]'\n  - id: rule:brand-new\n    reactant_smarts: '[#7]'\n",
    )
    found = ids(validate_tagger(tmp_path / "rules"))
    assert ("tagger_smarts_coverage", "rule:brand-new") in found
    assert ("tagger_smarts_coverage", mapped) not in found
    assert any(c == "tagger_sssom_orphan" for c, _ in found)


def test_tagger_empty_rules_dir_fails(tmp_path):
    report = validate_tagger(tmp_path)
    assert ("tagger_smarts_present", "xmet:4000213") in ids(report)


# --- CURIEs -----------------------------------------------------------------------


def test_curies_flags_retired_and_unknown_ids(tmp_path):
    f = write(tmp_path / "rules.yaml", "a: xmet:4000009\nb: xmet:0000000\nc: xmet:9999999\n")
    report = validate_curies([tmp_path])
    by_id = {x.subject_id: x for x in report.failures}
    assert "xmet:4000009" not in by_id
    assert by_id["xmet:0000000"].check_id == "curie_retired"
    assert by_id["xmet:0000000"].object_id == "xmet:4000000"
    assert by_id["xmet:9999999"].check_id == "curie_unknown"
    assert f"{f}:3" in by_id["xmet:9999999"].message


# --- Candidate SSSOM overrides ----------------------------------------------------


def test_sources_checks_candidate_sssom_then_restores(tmp_path):
    original = core.FOREST_SSSOM
    bad = tmp_path / "forest.sssom.tsv"
    bad.write_text(
        original.read_text()
        + "xmet:4000012\tskos:relatedMatch\txf:Hydroxylation\tsemapv:ManualMappingCuration\t\t\t\n"
    )
    with sources(forest_sssom=bad):
        report = validate_ontology()
    assert ("forest_rule_predicate", "xf:Hydroxylation") in ids(report)
    assert core.FOREST_SSSOM == original


# --- CLI --------------------------------------------------------------------------


def test_cli_exit_status(tmp_path):
    assert main(["ontology"]) == 0
    write(tmp_path / "x.md", "see xmet:9999999\n")
    assert main(["curies", str(tmp_path)]) == 1


def test_cli_json_report_shape(tmp_path, capsys):
    write(tmp_path / "x.md", "see xmet:9999999\n")
    main(["curies", str(tmp_path), "--json"])
    (report,) = json.loads(capsys.readouterr().out)
    assert report["name"] == "curies" and report["ok"] is False
    assert report["failures"][0]["check_id"] == "curie_unknown"
