#!/usr/bin/env python3
"""Dump BioTransformer reaction-type inventory for manual XMET curation.

Reads ``../xenosite-data/data/Biotransformer/reactions.csv`` (+ MetX classes
and MetX ``reaction_type`` literature labels) and writes
``data/mappings/biotransformer-inventory.tsv``. Does **not** guess SSSOM
matches — placement is manual (see README-biotransformer.md).

Grains:
- ``reaction_type`` — ``reactions.csv`` ``common_name`` (bundles ``_PATTERNn``)
- ``class`` — MetX ``biotransformation_type`` (Phase I/II/Gut)
- ``reaction_class`` — MetX short ``reaction_type`` labels (often no BTMR);
  highest-yield identity matches to XMET parent terms
"""

from __future__ import annotations

import csv
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BT_DIR = ROOT.parent / "xenosite-data" / "data" / "Biotransformer"
OUT = ROOT / "data/mappings/biotransformer-inventory.tsv"
STEM_RE = re.compile(r"_PATTERN\d+[A-Z]?$")

# Already curated — inventory marks these as placed (not "open").
PLACED_FILES = [
    ROOT / "data/mappings/xmet-biotransformer-common.sssom.tsv",
    ROOT / "data/mappings/xmet-biotransformer.sssom.tsv",
    ROOT / "data/mappings/biotransformer-proposed-terms.tsv",
    ROOT / "data/mappings/biotransformer-excluded.tsv",
    ROOT / "data/mappings/biotransformer-unassigned.tsv",
    ROOT / "data/mappings/biotransformer-eawag.tsv",
]


def load_placed() -> tuple[set[str], set[str]]:
    """Return (object_ids, labels) already curated in SSSOM/lists."""
    ids: set[str] = set()
    labels: set[str] = set()
    for path in PLACED_FILES:
        if not path.exists():
            continue
        with path.open() as fh:
            rows = csv.DictReader(
                (ln for ln in fh if not ln.startswith("#")), delimiter="\t"
            )
            for row in rows:
                for key in ("object_id", "bt_object_id"):
                    if row.get(key):
                        ids.add(row[key].strip())
                for key in ("bt_label", "object_label"):
                    if row.get(key):
                        labels.add(row[key].strip())
    return ids, labels


def all_stems(reaction_ids: list[str]) -> list[str]:
    return sorted({STEM_RE.sub("", rid) for rid in reaction_ids}, key=len)


def stem_of(reaction_ids: list[str]) -> str:
    stems = all_stems(reaction_ids)
    return stems[0] if stems else "UNKNOWN"


def main() -> None:
    if not BT_DIR.is_dir():
        raise SystemExit(f"BioTransformer data not found: {BT_DIR}")

    rxn = list(csv.DictReader((BT_DIR / "reactions.csv").open()))
    er = list(csv.DictReader((BT_DIR / "enzyme_reactions.csv").open()))
    be = list(csv.DictReader((BT_DIR / "biosystem_enzymes.csv").open()))
    human_enz = {r["enzyme_id"] for r in be if r["biosystem_id"] == "HUMAN"}
    gut_enz = {r["enzyme_id"] for r in be if r["biosystem_id"] == "GUTMICRO"}
    human_rxn = {
        r["reaction_id"] for r in er if r["source"] == "base" and r["enzyme_id"] in human_enz
    }
    gut_rxn = {
        r["reaction_id"] for r in er if r["source"] == "base" and r["enzyme_id"] in gut_enz
    }

    types: dict[str, dict] = {}
    for r in rxn:
        name = (r["common_name"] or "").strip()
        blank = False
        if not name:
            name = r["reaction_id"]
            blank = True
        if name not in types:
            types[name] = {
                "n": 0,
                "sources": set(),
                "rids": [],
                "btmrs": [],
                "human": False,
                "gut": False,
                "blank": blank,
            }
        t = types[name]
        t["n"] += 1
        t["sources"].add(r["source"])
        t["rids"].append(r["reaction_id"])
        if r.get("btmr_id"):
            t["btmrs"].append(r["btmr_id"])
        if r["reaction_id"] in human_rxn:
            t["human"] = True
        if r["reaction_id"] in gut_rxn:
            t["gut"] = True

    # MetX biosystem classes (Phase I/II/Gut) + literature reaction_type labels.
    # reaction_type without BTMR is the coarse "reaction class" grain that
    # bundles many observed biotransformations under one short chemist label.
    metx = BT_DIR / "metx_biotransformations.csv"
    class_counts: Counter[str] = Counter()
    rtype_counts: Counter[str] = Counter()
    rtype_no_btmr: Counter[str] = Counter()
    if metx.exists():
        for row in csv.DictReader(metx.open()):
            cls = (row.get("biotransformation_type") or "").strip()
            if cls:
                class_counts[cls] += 1
            rt = (row.get("reaction_type") or "").strip()
            if not rt:
                continue
            rtype_counts[rt] += 1
            btmr = (row.get("btmr_id") or "").strip().upper()
            if not btmr or btmr in {"N/A", "NA", "NONE"}:
                rtype_no_btmr[rt] += 1

    # Normalize spelling variants so inventory collapses demethylation typos etc.
    def rtype_slug(label: str) -> str:
        s = label.lower().strip()
        s = s.replace("dementhylation", "demethylation")
        s = s.replace("desmethylation", "demethylation")
        s = s.replace("desalkylation", "dealkylation")
        s = re.sub(r"[^a-z0-9]+", "_", s)
        return s.strip("_").upper()

    # Prefer labels that appear without BTMR (class grain); fall back to all
    # reaction_types whose slug is not already a reactions.csv common_name stem.
    cn_slugs = {rtype_slug(n) for n in types}
    rtype_acc: dict[str, dict] = {}
    for rt, n in rtype_counts.items():
        slug = rtype_slug(rt)
        no_btmr = rtype_no_btmr.get(rt, 0)
        # Keep literature class labels (any no-BTMR obs), or types whose slug
        # is not already a reactions.csv common_name.
        if no_btmr == 0 and slug in cn_slugs:
            continue
        acc = rtype_acc.setdefault(
            slug, {"label": rt, "n": 0, "no_btmr": 0, "label_score": (-1, -1)}
        )
        acc["n"] += n
        acc["no_btmr"] += no_btmr
        score = (no_btmr, n)
        if score > acc["label_score"]:
            acc["label"] = rt
            acc["label_score"] = score
    rtype_rows = {
        slug: {"label": a["label"], "n": a["n"], "no_btmr": a["no_btmr"]}
        for slug, a in rtype_acc.items()
    }

    placed_ids, placed_labels = load_placed()
    rows = []
    for name, t in types.items():
        stems = all_stems(t["rids"])
        oid = f"bt:{stems[0] if stems else 'UNKNOWN'}"
        is_placed = (
            name in placed_labels
            or oid in placed_ids
            or any(f"bt:{s}" in placed_ids for s in stems)
        )
        rows.append(
            {
                "bt_label": name,
                "bt_object_id": oid,
                "n_patterns": t["n"],
                "sources": ",".join(sorted(t["sources"])),
                "human": int(t["human"]),
                "gut": int(t["gut"]),
                "blank_name": int(t["blank"]),
                "placement": "placed" if is_placed else "open",
                "kind": "reaction_type",
            }
        )
    for cls, n in class_counts.items():
        slug = re.sub(r"\W+", "_", cls).upper()
        oid = f"bt.class:{slug}"
        rows.append(
            {
                "bt_label": cls,
                "bt_object_id": oid,
                "n_patterns": n,
                "sources": "metx_class",
                "human": int("Human" in cls and "Gut" not in cls),
                "gut": int("Gut" in cls),
                "blank_name": 0,
                "placement": "placed" if (oid in placed_ids or cls in placed_labels) else "open",
                "kind": "class",
            }
        )
    for slug, info in rtype_rows.items():
        oid = f"bt.rtype:{slug}"
        label = info["label"]
        is_placed = oid in placed_ids or label in placed_labels
        rows.append(
            {
                "bt_label": label,
                "bt_object_id": oid,
                "n_patterns": info["n"],
                "sources": "metx_reaction_type",
                "human": 1,
                "gut": 0,
                "blank_name": 0,
                "placement": "placed" if is_placed else "open",
                "kind": "reaction_class",
            }
        )
    # Ensure SSSOM-referenced bt.rtype:* rows exist even when the MetX label
    # coincides with a reactions.csv common_name (filtered above).
    have_rtypes = {r["bt_object_id"] for r in rows if r["kind"] == "reaction_class"}
    for oid in sorted(placed_ids):
        if not oid.startswith("bt.rtype:") or oid in have_rtypes:
            continue
        slug = oid.split(":", 1)[1]
        # Prefer a MetX label with this slug if present.
        label = next(
            (rt for rt in rtype_counts if rtype_slug(rt) == slug),
            slug.replace("_", " ").title(),
        )
        n = sum(c for rt, c in rtype_counts.items() if rtype_slug(rt) == slug)
        rows.append(
            {
                "bt_label": label,
                "bt_object_id": oid,
                "n_patterns": n or 0,
                "sources": "metx_reaction_type",
                "human": 1,
                "gut": 0,
                "blank_name": 0,
                "placement": "placed",
                "kind": "reaction_class",
            }
        )

    rows.sort(key=lambda r: (-int(r["n_patterns"]), r["bt_label"].lower()))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as fh:
        fields = [
            "bt_label",
            "bt_object_id",
            "kind",
            "n_patterns",
            "sources",
            "human",
            "gut",
            "blank_name",
            "placement",
        ]
        w = csv.DictWriter(fh, fieldnames=fields, delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)

    open_n = sum(1 for r in rows if r["placement"] == "open")
    print(f"wrote {len(rows)} inventory rows → {OUT.relative_to(ROOT)}")
    print(f"  placed labels/ids seen: {len(placed_labels)} labels, {len(placed_ids)} ids")
    print(f"  still open: {open_n}")


if __name__ == "__main__":
    main()
