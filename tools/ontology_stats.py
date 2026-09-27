#!/usr/bin/env python3
"""Heads-up ontology statistics for XRM (terminal summary).

Reads authoring YAML (+ optional SKOS/mappings/assignments) and prints
spine inventory vs guidance bands, label counts, and mapping tallies.

Usage:
  make ontology-stats
  uv run python crates/xenosite-tagger/tools/ontology_stats.py
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
YAML_PATH = ROOT / "data/ontology/xrm.yaml"
SKOS_PATH = ROOT / "data/ontology/xrm.skos.jsonld"
MAP_DIR = ROOT / "data/mappings"
ASSIGN_DIR = ROOT / "data/assignments"

# From ANNOTATION.md category bands (floor guidance, not hard caps)
BANDS: list[tuple[str, int, int]] = [
    ("metabolism phase", 10, 20),
    ("chemical transformation", 90, 140),
    ("phase I reaction family", 25, 40),
    ("phase II conjugation family", 40, 70),
    ("reactive metabolite family", 70, 110),
    ("site type", 60, 100),
    ("structural delta", 35, 60),
    ("medchem liability", 40, 70),
    ("evidence", 30, 50),
    ("biological context", 40, 100),
    ("rule provenance", 20, 40),
    ("leaving group", 20, 40),
    ("pharmacological role", 10, 25),
    ("annotation about", 5, 15),
    ("ambiguity and underspecification", 5, 25),
    ("product status", 10, 30),
    ("Metabolic Forest map", 0, 9999),  # alias spine; no band pressure
]


def nearest_spine(
    cid: str,
    spines: dict[str, str],
    by_id: dict[str, dict],
    cache: dict[str, str | None],
) -> str | None:
    if cid in cache:
        return cache[cid]
    if cid in spines:
        cache[cid] = cid
        return cid
    seen: set[str] = set()

    def walk(x: str) -> str | None:
        if x in spines:
            return x
        if x in seen or x not in by_id:
            return None
        seen.add(x)
        for p in by_id[x].get("parents") or []:
            r = walk(p)
            if r:
                return r
        return None

    cache[cid] = walk(cid)
    return cache[cid]


def band_marker(n: int, lo: int, hi: int) -> str:
    """Guidance bands are a usefulness floor, not a cap — above-band is fine."""
    if hi >= 9999:
        return "alias"
    if n < lo:
        return f"below floor ({lo}–{hi})"
    if n > hi:
        return f"above band ({lo}–{hi}; ok if clear)"
    return f"in band ({lo}–{hi})"


def count_mapping_rows(path: Path) -> int:
    n = 0
    for line in path.read_text().splitlines():
        s = line.strip()
        if not s or s.startswith("#") or s.startswith("subject_id") or s.startswith("reaction_id"):
            continue
        n += 1
    return n


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--yaml", type=Path, default=YAML_PATH)
    p.add_argument("--json", action="store_true", help="Also emit JSON blob on stdout after text")
    args = p.parse_args()

    raw = yaml.safe_load(args.yaml.read_text())
    spines = {s["id"]: s["preferred_label"] for s in raw["spines"]}
    concepts = raw["concepts"]
    by_id = {c["id"]: c for c in concepts}
    for s in raw["spines"]:
        by_id[s["id"]] = {**s, "parents": []}

    cache: dict[str, str | None] = {}
    by_spine: Counter[str] = Counter()
    n_syn = 0
    n_with_syn = 0
    n_related = 0
    n_orphan_parent = 0
    n_no_parent = 0
    leaves = 0
    children_of: Counter[str] = Counter()

    for c in concepts:
        for p in c.get("parents") or []:
            children_of[p] += 1
            if p not in by_id:
                n_orphan_parent += 1
        if not c.get("parents"):
            n_no_parent += 1
        syns = c.get("synonyms") or []
        if syns:
            n_with_syn += 1
            n_syn += len(syns)
        if c.get("related_match"):
            n_related += 1
        sid = nearest_spine(c["id"], spines, by_id, cache)
        by_spine[spines.get(sid or "", "none")] += 1

    for c in concepts:
        if children_of[c["id"]] == 0:
            leaves += 1

    n_labels = len(concepts) + n_syn
    skos_n = None
    if SKOS_PATH.exists():
        try:
            skos = json.loads(SKOS_PATH.read_text())
            skos_n = sum(1 for n in skos.get("@graph", []) if n.get("type") == "skos:Concept")
        except Exception:
            skos_n = None

    map_counts = {}
    if MAP_DIR.is_dir():
        for f in sorted(MAP_DIR.glob("*.tsv")):
            map_counts[f.name] = count_mapping_rows(f)

    assign_counts = {}
    if ASSIGN_DIR.is_dir():
        for f in sorted(ASSIGN_DIR.glob("*.jsonl")):
            assign_counts[f.name] = sum(
                1 for line in f.read_text().splitlines() if line.strip()
            )

    # --- print ---
    print("XRM ontology stats")
    print(f"  source: {args.yaml.relative_to(ROOT) if args.yaml.is_relative_to(ROOT) else args.yaml}")
    print(f"  spines:   {len(spines)}")
    print(f"  concepts: {len(concepts)}  (leaves {leaves}, internal {len(concepts) - leaves})")
    print(f"  labels:   {n_labels}  (pref {len(concepts)} + alt/syn {n_syn}; {n_with_syn} concepts have synonyms)")
    print(f"  related_match on {n_related} concepts")
    if n_no_parent or n_orphan_parent:
        print(f"  warnings: no-parent={n_no_parent}  missing-parent-refs={n_orphan_parent}")
    if skos_n is not None:
        delta = skos_n - len(concepts)
        note = "in sync" if delta == 0 else f"SKOS−YAML={delta:+d} (re-export?)"
        print(f"  skos.jsonld concepts: {skos_n}  ({note})")

    print("\nConcepts by spine (nearest root) vs guidance band")
    print("(bands are a usefulness floor, not a cap — more clear terms are welcome):")
    band_map = {name: (lo, hi) for name, lo, hi in BANDS}
    for name, _lo, _hi in BANDS:
        n = by_spine.get(name, 0)
        lo, hi = band_map[name]
        print(f"  {n:4d}  {name:<36}  {band_marker(n, lo, hi)}")
    extras = sorted(set(by_spine) - {n for n, _, _ in BANDS} - {"none"})
    for name in extras:
        print(f"  {by_spine[name]:4d}  {name:<36}  (no band)")
    if by_spine.get("none"):
        print(f"  {by_spine['none']:4d}  {'(unattached)':<36}  check parents")

    if map_counts:
        print("\nMappings:")
        for name, n in map_counts.items():
            print(f"  {n:4d}  {name}")
    if assign_counts:
        print("\nAssignments:")
        for name, n in assign_counts.items():
            print(f"  {n:4d}  {name}")

    # compact guidance floor reminder
    chem = by_spine.get("chemical transformation", 0)
    total_chemist = sum(
        by_spine.get(n, 0)
        for n, _, hi in BANDS
        if hi < 9999 and n != "Metabolic Forest map"
    )
    print(f"\nChemist-facing concepts (excl. Forest map alias): {total_chemist}")
    print(f"Chemical transformation core: {chem}")

    if args.json:
        payload = {
            "n_spines": len(spines),
            "n_concepts": len(concepts),
            "n_leaves": leaves,
            "n_labels": n_labels,
            "n_synonyms": n_syn,
            "by_spine": dict(by_spine),
            "mappings": map_counts,
            "assignments": assign_counts,
            "skos_concepts": skos_n,
        }
        print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
