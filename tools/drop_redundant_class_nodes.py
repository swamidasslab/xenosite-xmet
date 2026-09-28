#!/usr/bin/env python3
"""Drop redundant reaction-class '* class' nodes that duplicate chemist leaves.

Scope: reaction-class shelf only (spine 2). Does not touch Forest patterns,
descriptor thinning, or other spines.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
YAML_PATH = ROOT / "data/ontology/xmet.yaml"
REMAP_PATH = ROOT / "data/mappings/xmet-id-remap.tsv"
FOREST_SSSOM = ROOT / "data/mappings/xmet-forest.sssom.tsv"
UNPLACED = "xmet:4000213"


def norm_label(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"\s+class$", "", s)
    s = s.replace("_", " ")
    s = re.sub(r"\s+", " ", s)
    return s


# Explicit synonym collapses where labels differ slightly.
LABEL_ALIASES: dict[str, str] = {
    "gsh conjugation": "glutathione conjugation",
    "glutathione conjugation class": "glutathione conjugation",
    "epoxide gsh conjugation": "epoxide glutathionation",
    "michael gsh conjugation": "michael glutathionation",
    "halide-displacement gsh conjugation": "halide displacement glutathionation",
    "halide displacement gsh conjugation": "halide displacement glutathionation",
    "phosphorylation conjugation": "phosphorylation",
    "iminium formation": "iminium ion formation",
    "n-oxidation": "nitrogen oxidation",
    "s-oxidation": "sulfur oxidation",
    "single-to-double bond dehydrogenation": "single- to double-bond dehydrogenation",
    "double-to-triple bond dehydrogenation": "double- to triple-bond dehydrogenation",
    "alcohol dehydrogenation": "alcohol oxidation",
}


def load() -> dict[str, Any]:
    return yaml.safe_load(YAML_PATH.read_text())


def chemist_label_index(concepts: list[dict[str, Any]]) -> dict[str, str]:
    """preferred_label / synonym → first non-9*, non-12xxxx-class, non-13xxxx-class id."""
    idx: dict[str, str] = {}
    for c in concepts:
        cid = c["id"]
        if cid.startswith("xmet:9"):
            continue
        # Prefer non-parking class inventory IDs as targets
        if cid.startswith(("xmet:12", "xmet:13")) and cid[5:7] in {"00", "01", "02"}:
            # still allow as target only if no better exists later
            pass
        lab = norm_label(c.get("preferred_label") or "")
        if lab and lab not in idx:
            idx[lab] = cid
        for syn in c.get("synonyms") or []:
            s = norm_label(syn)
            if s and s not in idx:
                idx[s] = cid
    # Re-pass preferring non-12/13 inventory class nodes
    for c in concepts:
        cid = c["id"]
        if cid.startswith(("xmet:9", "xmet:12", "xmet:13")):
            continue
        lab = norm_label(c.get("preferred_label") or "")
        if lab:
            idx[lab] = cid
        for syn in c.get("synonyms") or []:
            s = norm_label(syn)
            if s:
                idx[s] = cid
    return idx


def is_redundant_class_node(c: dict[str, Any]) -> bool:
    cid = c["id"]
    lab = c.get("preferred_label") or ""
    if cid.startswith(("xmet:12001", "xmet:12002", "xmet:13001")):
        return True
    if lab.lower().endswith(" class") and UNPLACED in (c.get("parents") or []):
        return True
    return False


def resolve_target(c: dict[str, Any], idx: dict[str, str]) -> str | None:
    lab = norm_label(c.get("preferred_label") or "")
    candidates = [lab, LABEL_ALIASES.get(lab, ""), LABEL_ALIASES.get(c.get("preferred_label", "").lower(), "")]
    for syn in c.get("synonyms") or []:
        candidates.append(norm_label(syn))
        candidates.append(LABEL_ALIASES.get(norm_label(syn), ""))
    for key in candidates:
        if not key:
            continue
        key = LABEL_ALIASES.get(key, key)
        tgt = idx.get(key)
        if tgt and tgt != c["id"]:
            return tgt
    return None


def scrub_sssom(dropped: set[str]) -> None:
    if not FOREST_SSSOM.exists() or not dropped:
        return
    lines = FOREST_SSSOM.read_text().splitlines()
    out: list[str] = []
    removed = 0
    for ln in lines:
        if ln.startswith("#") or not ln.strip() or "\t" not in ln:
            out.append(ln)
            continue
        # header or row
        subj = ln.split("\t", 1)[0]
        if subj in dropped:
            removed += 1
            continue
        out.append(ln)
    FOREST_SSSOM.write_text("\n".join(out) + "\n")
    print(f"forest SSSOM: removed {removed} rows for dropped subjects")


def main() -> None:
    data = load()
    concepts = data["concepts"]
    idx = chemist_label_index(concepts)

    drop_ids: list[str] = []
    remap_rows: list[dict[str, str]] = []
    no_target: list[str] = []

    for c in concepts:
        if not is_redundant_class_node(c):
            continue
        # Only drop if currently parked or clearly inventory class
        parents = c.get("parents") or []
        if UNPLACED not in parents and not c["id"].startswith(("xmet:12001", "xmet:12002", "xmet:13001")):
            continue
        tgt = resolve_target(c, idx)
        if tgt:
            drop_ids.append(c["id"])
            remap_rows.append(
                {
                    "old_id": c["id"],
                    "new_id": tgt,
                    "change_type": "merged",
                    "note": f"redundant class node → {by_id_label(concepts, tgt)}",
                }
            )
        else:
            no_target.append(f"{c['id']} {c.get('preferred_label')}")

    by = {c["id"]: c for c in concepts}
    keep = [c for c in concepts if c["id"] not in set(drop_ids)]
    # Also drop parents refs to dropped ids elsewhere
    dropped = set(drop_ids)
    for c in keep:
        ps = [p for p in (c.get("parents") or []) if p not in dropped]
        c["parents"] = ps

    data["concepts"] = keep
    YAML_PATH.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=100))

    with REMAP_PATH.open("a", newline="") as fh:
        w = csv.DictWriter(
            fh, fieldnames=["old_id", "new_id", "change_type", "note"], delimiter="\t"
        )
        for row in remap_rows:
            w.writerow(row)

    scrub_sssom(dropped)

    parked = sum(1 for c in keep if UNPLACED in (c.get("parents") or []))
    print(f"dropped redundant class nodes: {len(drop_ids)}")
    for r in remap_rows:
        print(f"  {r['old_id']} → {r['new_id']}  ({r['note']})")
    if no_target:
        print(f"kept (no chemist target yet): {len(no_target)}")
        for line in no_target:
            print(f"  {line}")
    print(f"remaining under unplaced: {parked}")


def by_id_label(concepts: list[dict[str, Any]], cid: str) -> str:
    for c in concepts:
        if c["id"] == cid:
            return c.get("preferred_label") or cid
    return cid


if __name__ == "__main__":
    main()
