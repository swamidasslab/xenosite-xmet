"""Checks of a reaction-tagger rules directory against XMET's tagger SSSOM.

Run from the tagger repository to confirm that every SMARTS rule has an
exactMatch home in XMET and that no SSSOM row points at a removed rule.
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

import yaml

from xenosite.xmet.validate import core
from xenosite.xmet.validate.core import Finding

RULE_FILES = ("xenobiotic.rules.yaml", "structural.rules.yaml")


def load_smarts_rule_ids(rules_dir: Path) -> list[str]:
    """IDs of rules that carry reactant or product SMARTS."""
    ids: list[str] = []
    for name in RULE_FILES:
        path = rules_dir / name
        if not path.exists():
            continue
        data = yaml.safe_load(path.read_text()) or {}
        for rule in data.get("rules") or []:
            if rule.get("reactant_smarts") or rule.get("product_smarts"):
                ids.append(rule["id"])
    return ids


def check_rules_present(findings: list[Finding], smarts_ids: list[str], rules_dir: Path) -> None:
    if not smarts_ids:
        findings.append(
            Finding("tagger_smarts_present", "xmet:4000213", f"no SMARTS rules found under {rules_dir} ({', '.join(RULE_FILES)})")
        )


def check_smarts_coverage(
    findings: list[Finding], smarts_ids: list[str], by_obj: dict[str, list[dict[str, str]]]
) -> None:
    """Every SMARTS rule has an exactMatch row in the tagger SSSOM."""
    for rid in smarts_ids:
        if not any(r["predicate_id"] == "skos:exactMatch" for r in by_obj.get(rid) or []):
            findings.append(
                Finding(
                    "tagger_smarts_coverage",
                    "xmet:4000213",
                    "SMARTS rule missing exactMatch row in xmet-tagger.sssom.tsv",
                    rid,
                )
            )


def check_sssom_orphans(
    findings: list[Finding], smarts_ids: list[str], by_obj: dict[str, list[dict[str, str]]]
) -> None:
    """SSSOM rows whose rule is no longer a SMARTS rule in the tagger."""
    live = set(smarts_ids)
    for obj, rows in by_obj.items():
        if obj.startswith("rule:") and obj not in live:
            findings.append(
                Finding("tagger_sssom_orphan", rows[0]["subject_id"], "SSSOM object not a current SMARTS rule", obj)
            )


def tagger_findings(rules_dir: Path) -> list[Finding]:
    """All tagger-rules checks for one rules directory."""
    smarts_ids = load_smarts_rule_ids(rules_dir)
    by_obj: dict[str, list[dict[str, str]]] = defaultdict(list)
    for r in core.load_sssom(core.TAGGER_SSSOM):
        by_obj[r["object_id"]].append(r)
    findings: list[Finding] = []
    check_rules_present(findings, smarts_ids, rules_dir)
    check_smarts_coverage(findings, smarts_ids, by_obj)
    check_sssom_orphans(findings, smarts_ids, by_obj)
    return findings
