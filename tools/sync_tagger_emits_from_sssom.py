#!/usr/bin/env python3
"""Rewrite tagger RuleSet emits from xmet-tagger.sssom (subrepo SoT).

For each SMARTS rule with a SSSOM row, set ``emit`` to the live reaction-class
subject plus any YAML ``always_with`` companions on that subject. Drop CURIEs
that are not live XMET (or non-xmet external kept as-is only if already live
in the emit list — xmet unknowns are dropped).

Rules without SSSOM: filter emit/expect_emit to live xmet only (may empty).

Does not invent Forest pattern CURIEs. Writes sibling tagger YAML in place.
Override rules dir with XMET_TAGGER_RULES_DIR.
"""

from __future__ import annotations

import csv
import io
import os
import sys
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML

ROOT = Path(__file__).resolve().parents[1]
YAML_PATH = ROOT / "data/ontology/xmet.yaml"
TAGGER_SSSOM = ROOT / "data/mappings/xmet-tagger.sssom.tsv"
DEFAULT_RULES_DIR = ROOT.parent / "crates" / "xenosite-tagger" / "data" / "rules"
RULE_FILES = ("xenobiotic.rules.yaml", "structural.rules.yaml")
COVERAGE_TSVS = (
    "coverable_terms.tsv",
    "strong_match_terms.tsv",
    "strong_match_coverage.tsv",
    "coverage_allowlist.tsv",
)


def rules_dir() -> Path:
    override = os.environ.get("XMET_TAGGER_RULES_DIR")
    return Path(override) if override else DEFAULT_RULES_DIR


def load_sssom(path: Path) -> dict[str, str]:
    raw = path.read_text().splitlines()
    hdr = next(i for i, line in enumerate(raw) if line.startswith("subject_id"))
    rows = csv.DictReader(io.StringIO("\n".join(raw[hdr:])), delimiter="\t")
    out: dict[str, str] = {}
    for row in rows:
        obj, sub = row.get("object_id", ""), row.get("subject_id", "")
        if obj and sub:
            out[obj] = sub
    return out


def load_live_and_always_with() -> tuple[set[str], dict[str, list[str]]]:
    data = YAML(typ="safe").load(YAML_PATH.read_text())
    live: set[str] = set()
    always: dict[str, list[str]] = {}
    for c in data["concepts"]:
        cid = c["id"]
        live.add(cid)
        aw = c.get("always_with") or []
        if isinstance(aw, str):
            aw = [aw]
        if aw:
            always[cid] = list(aw)
    return live, always


def has_smarts(rule: dict[str, Any]) -> bool:
    return bool(rule.get("reactant_smarts") or rule.get("product_smarts"))


def filter_emits(emits: list[Any], live: set[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for e in emits or []:
        if not isinstance(e, str):
            continue
        if e.startswith("xmet:"):
            if e not in live:
                continue
        # keep external CURIEs as-is (thesaurus may still know them)
        if e not in seen:
            seen.add(e)
            out.append(e)
    return out


def build_emit(rule_id: str, sssom: dict[str, str], live: set[str], always: dict[str, list[str]]) -> list[str] | None:
    """Return new emit list, or None to only filter existing."""
    home = sssom.get(rule_id)
    if not home:
        return None
    if home not in live:
        raise SystemExit(f"SSSOM subject not live: {home} for {rule_id}")
    emits = [home]
    for aw in always.get(home, []):
        if aw in live and aw not in emits:
            emits.append(aw)
    return emits


def sync_rules_file(
    path: Path,
    sssom: dict[str, str],
    live: set[str],
    always: dict[str, list[str]],
) -> dict[str, int]:
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.width = 4096
    data = yaml.load(path.read_text())
    stats = {
        "rules": 0,
        "sssom_set": 0,
        "filtered": 0,
        "emptied": 0,
        "missing_sssom_smarts": 0,
    }
    missing: list[str] = []
    for rule in data.get("rules") or []:
        stats["rules"] += 1
        rid = rule.get("id", "")
        new_emit = build_emit(rid, sssom, live, always)
        if new_emit is not None:
            rule["emit"] = new_emit
            stats["sssom_set"] += 1
        else:
            old = list(rule.get("emit") or [])
            filtered = filter_emits(old, live)
            if filtered != old:
                stats["filtered"] += 1
            rule["emit"] = filtered
            if has_smarts(rule) and rid.startswith("rule:"):
                stats["missing_sssom_smarts"] += 1
                missing.append(rid)
            if not filtered and old:
                stats["emptied"] += 1
        # examples expect_emit
        for ex in rule.get("examples") or []:
            if isinstance(ex, dict) and "expect_emit" in ex:
                ex["expect_emit"] = filter_emits(list(ex.get("expect_emit") or []), live)
        if "expect_emit" in rule:
            rule["expect_emit"] = filter_emits(list(rule.get("expect_emit") or []), live)

    with path.open("w") as fh:
        yaml.dump(data, fh)

    if missing:
        print(f"WARN {path.name}: {len(missing)} SMARTS rules lack SSSOM home:", file=sys.stderr)
        for rid in missing[:20]:
            print(f"  {rid}", file=sys.stderr)
        if len(missing) > 20:
            print(f"  ... +{len(missing) - 20} more", file=sys.stderr)
    return stats


def sync_coverage_tsv(path: Path, live: set[str]) -> tuple[int, int]:
    if not path.exists():
        return 0, 0
    text = path.read_text()
    lines = text.splitlines(keepends=True)
    if not lines:
        return 0, 0
    kept: list[str] = []
    dropped = 0
    # keep header
    kept.append(lines[0] if lines[0].endswith("\n") else lines[0] + "\n")
    for line in lines[1:]:
        raw = line.strip("\n")
        if not raw.strip() or raw.startswith("#"):
            kept.append(line if line.endswith("\n") else line + "\n")
            continue
        # first column is usually the CURIE / term id
        term = raw.split("\t")[0].strip()
        if term.startswith("xmet:") and term not in live:
            dropped += 1
            continue
        kept.append(line if line.endswith("\n") else line + "\n")
    path.write_text("".join(kept))
    return len(kept) - 1, dropped


def main() -> int:
    directory = rules_dir()
    if not directory.is_dir():
        print(f"tagger rules dir not found: {directory}", file=sys.stderr)
        return 1

    live, always = load_live_and_always_with()
    sssom = load_sssom(TAGGER_SSSOM)
    print(f"live concepts={len(live)} sssom rules={len(sssom)} always_with subjects={len(always)}")

    for name in RULE_FILES:
        path = directory / name
        stats = sync_rules_file(path, sssom, live, always)
        print(f"{name}: {stats}")

    for name in COVERAGE_TSVS:
        path = directory / name
        kept, dropped = sync_coverage_tsv(path, live)
        print(f"{name}: kept_rows≈{kept} dropped={dropped}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
