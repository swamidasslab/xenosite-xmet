#!/usr/bin/env python3
"""Drop deferred / out-of-scope spines from live XMET (redesign this-version scope).

KEEP: disposition stage, reaction class, reaction descriptor, concept relation (+ root).
Also drop disposition extras: sequential / first-pass / intermediate metabolite.
Scrub SSSOM rows whose subject is retired. Append remap retired rows.

Backup: git history (no artifacts copy).
"""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
YAML_PATH = ROOT / "data/ontology/xmet.yaml"
REMAP_PATH = ROOT / "data/mappings/xmet-id-remap.tsv"
SSSOM_PATHS = [
    ROOT / "data/mappings/xmet-forest.sssom.tsv",
    ROOT / "data/mappings/xmet-external.sssom.tsv",
    ROOT / "data/mappings/xmet-mop.sssom.tsv",
    ROOT / "data/mappings/xmet-mesh.sssom.tsv",
    ROOT / "data/mappings/xmet-udm.sssom.tsv",
]

# Spine roots to remove entirely (plan: deferred / OUT OF SCOPE this version).
DROP_SPINE_ROOTS = {
    "xmet:1200000",  # legacy phase I reaction family
    "xmet:1300000",  # legacy phase II conjugation family
    "xmet:1400000",  # medchem liability
    "xmet:1500000",  # reactive metabolite family
    "xmet:1600000",  # site type
    "xmet:1800000",  # product status
    "xmet:1900000",  # rule provenance
    "xmet:2000000",  # evidence
    "xmet:2100000",  # biological context
    "xmet:2300000",  # pharmacological role
    "xmet:2400000",  # annotation about
    "xmet:2500000",  # metabolite product family
    "xmet:6000000",  # ambiguity and underspecification
    "xmet:9000000",  # Metabolic Forest map
}

# Disposition children to drop (plan spine 1).
DROP_DISPOSITION_LABELS = {
    "sequential metabolism",
    "first-pass metabolism",
    "intermediate metabolite formation",
}

KEEP_SPINE_IDS = {
    "xmet:4000212",
    "xmet:4000213",
    "xmet:4000263",
    "xmet:4000281",
}


def subtree(cid: str, children: dict[str, list[str]]) -> set[str]:
    out: set[str] = set()
    stack = [cid]
    while stack:
        cur = stack.pop()
        if cur in out:
            continue
        out.add(cur)
        stack.extend(children.get(cur) or [])
    return out


def scrub_sssom(path: Path, dropped: set[str]) -> int:
    if not path.exists():
        return 0
    lines = path.read_text().splitlines()
    out: list[str] = []
    removed = 0
    header_done = False
    for ln in lines:
        if ln.startswith("#") or not ln.strip():
            out.append(ln)
            continue
        if not header_done and ln.startswith("subject_id"):
            out.append(ln)
            header_done = True
            continue
        sub = ln.split("\t", 1)[0]
        if sub in dropped:
            removed += 1
            continue
        out.append(ln)
    path.write_text("\n".join(out) + ("\n" if out else ""))
    return removed


def main() -> None:
    data = yaml.safe_load(YAML_PATH.read_text())
    concepts: list[dict[str, Any]] = data["concepts"]
    by = {c["id"]: c for c in concepts}
    children: dict[str, list[str]] = defaultdict(list)
    for c in concepts:
        for p in c.get("parents") or []:
            children[p].append(c["id"])

    drop: set[str] = set()
    for root in DROP_SPINE_ROOTS:
        if root in by:
            drop |= subtree(root, children)

    for c in concepts:
        if c.get("preferred_label") in DROP_DISPOSITION_LABELS:
            drop.add(c["id"])
            drop |= subtree(c["id"], children)

    # Spines list: keep only in-scope + any non-concept metadata we still want
    old_spines = list(data.get("spines") or [])
    new_spines = [s for s in old_spines if s.get("id") in KEEP_SPINE_IDS]
    # Preserve order of KEEP as in plan
    order = ["xmet:4000212", "xmet:4000213", "xmet:4000263", "xmet:4000281"]
    by_spine = {s["id"]: s for s in new_spines}
    data["spines"] = [by_spine[i] for i in order if i in by_spine]

    kept: list[dict[str, Any]] = []
    for c in concepts:
        if c["id"] in drop:
            continue
        parents = [p for p in (c.get("parents") or []) if p not in drop]
        c["parents"] = parents
        if not parents and c["id"] != "xmet:4000000":
            # orphaned non-root: should not happen for KEEP subtrees; park warning
            print(f"WARN orphan after drop: {c['id']} {c.get('preferred_label')}")
        kept.append(c)

    data["concepts"] = kept
    YAML_PATH.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=100))

    remap_rows = [
        {
            "old_id": cid,
            "new_id": "",
            "change_type": "retired",
            "note": "deferred spine wiped (out of scope this redesign version)",
        }
        for cid in sorted(drop)
    ]
    with REMAP_PATH.open("a", newline="") as fh:
        w = csv.DictWriter(
            fh, fieldnames=["old_id", "new_id", "change_type", "note"], delimiter="\t"
        )
        for row in remap_rows:
            w.writerow(row)

    print(f"retired concepts: {len(drop)}")
    print(f"remaining concepts: {len(kept)}")
    print(f"spines kept: {[s['preferred_label'] for s in data['spines']]}")

    for path in SSSOM_PATHS:
        n = scrub_sssom(path, drop)
        print(f"SSSOM scrub {path.name}: removed {n} rows")


if __name__ == "__main__":
    main()
