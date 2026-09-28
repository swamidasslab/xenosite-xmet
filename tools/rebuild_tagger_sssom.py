#!/usr/bin/env python3
"""Rebuild xmet-tagger.sssom.tsv: SMARTS rules → primary reaction-class homes.

Primary home = first `emit` CURIE that resolves (via live id or remap) to a
concept under the reaction-class spine. Emit order is authorial priority;
descriptor/disposition/dead CURIEs are skipped.

Tagger RuleSet YAML lives in the sibling xenosite-tagger crate
(`../crates/xenosite-tagger/data/rules/`). Override with XMET_TAGGER_RULES_DIR.
"""

from __future__ import annotations

import csv
import os
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
YAML_PATH = ROOT / "data/ontology/xmet.yaml"
REMAP_PATH = ROOT / "data/mappings/xmet-id-remap.tsv"
OUT_PATH = ROOT / "data/mappings/xmet-tagger.sssom.tsv"
REACTION_CLASS = "xmet:4000213"

DEFAULT_RULES_DIR = ROOT.parent / "crates" / "xenosite-tagger" / "data" / "rules"
RULE_FILES = ("xenobiotic.rules.yaml", "structural.rules.yaml")

FIELDS = [
    "subject_id",
    "predicate_id",
    "object_id",
    "mapping_justification",
    "subject_label",
    "object_label",
]


def rules_dir() -> Path:
    override = os.environ.get("XMET_TAGGER_RULES_DIR")
    return Path(override) if override else DEFAULT_RULES_DIR


def load_remap(live: set[str]) -> dict[str, str]:
    """Resolve stale emits via remap ledger (renumbered/merged/moved) + renumber TSV."""
    remap: dict[str, str] = {}
    renumber_path = ROOT / "data/mappings/xmet-id-renumber.tsv"
    if renumber_path.exists():
        with renumber_path.open() as fh:
            for row in csv.DictReader(fh, delimiter="\t"):
                old, new = row.get("old_id", ""), row.get("new_id", "")
                if old and new and new in live:
                    remap[old] = new
    if REMAP_PATH.exists():
        with REMAP_PATH.open() as fh:
            for row in csv.DictReader(fh, delimiter="\t"):
                old, new, ctype = row.get("old_id", ""), row.get("new_id", ""), row.get("change_type", "")
                if old and new and new in live and ctype in ("merged", "moved", "renumbered"):
                    remap[old] = new
    return remap


def parents_map(concepts: list[dict[str, Any]]) -> dict[str, list[str]]:
    return {c["id"]: list(c.get("parents") or []) for c in concepts}


def ancestors(cid: str, pm: dict[str, list[str]], memo: dict[str, set[str]]) -> set[str]:
    if cid in memo:
        return memo[cid]
    out: set[str] = set()
    for p in pm.get(cid, []):
        out.add(p)
        out |= ancestors(p, pm, memo)
    memo[cid] = out
    return out


def in_reaction_class(cid: str, live: set[str], pm: dict[str, list[str]], memo: dict[str, set[str]]) -> bool:
    return cid in live and (cid == REACTION_CLASS or REACTION_CLASS in ancestors(cid, pm, memo))


def has_smarts(rule: dict[str, Any]) -> bool:
    return bool(rule.get("reactant_smarts") or rule.get("product_smarts"))


def primary_rc(
    rule: dict[str, Any],
    live: set[str],
    remap: dict[str, str],
    pm: dict[str, list[str]],
    memo: dict[str, set[str]],
) -> str | None:
    for emit in rule.get("emit") or []:
        rid = emit if emit in live else remap.get(emit)
        if rid and in_reaction_class(rid, live, pm, memo):
            return rid
    return None


def load_smarts_rules(directory: Path) -> list[dict[str, Any]]:
    rules: list[dict[str, Any]] = []
    for name in RULE_FILES:
        path = directory / name
        if not path.exists():
            raise FileNotFoundError(f"missing tagger rules file: {path}")
        data = yaml.safe_load(path.read_text())
        for rule in data.get("rules") or []:
            if has_smarts(rule):
                rules.append(rule)
    return rules


def main() -> int:
    directory = rules_dir()
    if not directory.is_dir():
        print(f"tagger rules dir not found: {directory}", file=sys.stderr)
        print("set XMET_TAGGER_RULES_DIR or keep the sibling crate checkout", file=sys.stderr)
        return 1

    data = yaml.safe_load(YAML_PATH.read_text())
    concepts = data["concepts"]
    by_id = {c["id"]: c for c in concepts}
    live = set(by_id)
    pm = parents_map(concepts)
    memo: dict[str, set[str]] = {}
    remap = load_remap(live)

    smarts = load_smarts_rules(directory)
    rows: list[dict[str, str]] = []
    missing: list[str] = []
    for rule in smarts:
        rid = rule["id"]
        home = primary_rc(rule, live, remap, pm, memo)
        if home is None:
            missing.append(rid)
            continue
        rows.append(
            {
                "subject_id": home,
                "predicate_id": "skos:exactMatch",
                "object_id": rid,
                "mapping_justification": "semapv:ManualMappingCuration",
                "subject_label": by_id[home]["preferred_label"],
                "object_label": rid.removeprefix("rule:"),
            }
        )

    if missing:
        print(f"ERROR: {len(missing)} SMARTS rules have no live reaction-class emit:", file=sys.stderr)
        for rid in missing:
            print(f"  {rid}", file=sys.stderr)
        return 1

    rows.sort(key=lambda r: (r["object_id"], r["subject_id"]))

    header = (
        "# Xenosite-tagger SMARTS rules ↔ XMET reaction-class homes.\n"
        "# Primary home = first emit CURIE under reaction class (remap-resolved).\n"
        "# Object CURIEs are opaque rule:… ids from the tagger RuleSet YAML.\n"
    )
    with OUT_PATH.open("w", newline="") as fh:
        fh.write(header)
        writer = csv.DictWriter(fh, fieldnames=FIELDS, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    print(f"wrote {len(rows)} mappings → {OUT_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
