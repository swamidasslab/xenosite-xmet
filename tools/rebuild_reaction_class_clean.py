#!/usr/bin/env python3
"""Rebuild reaction-class spine from locked skeleton; import Forest PhaseOneRS + conjugation.

Strategy:
  1. Keep disposition / descriptor / relation spines as-is.
  2. Define clean reaction-class parent map (oxidation/reduction/isoredox + colors + forks).
  3. Import PhaseOneRS rules (and key conjugations) under the correct color/fork.
  4. Anything else currently under reaction class → park at unplaced shelf (not lost).
  5. Prefer chemist CURIEs (non-xmet:9*) as Forest SSSOM subjects where both exist.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
YAML_PATH = ROOT / "data/ontology/xmet.yaml"
FOREST_SSSOM = ROOT / "data/mappings/xmet-forest.sssom.tsv"
REMAP_PATH = ROOT / "data/mappings/xmet-id-remap.tsv"
ARTIFACTS = ROOT / "artifacts"

REACTION_CLASS = "xmet:4000213"
OXIDATION = "xmet:4000009"
SO = "xmet:4000004"
UO = "xmet:4000005"
DH = "xmet:4000006"
HD = "xmet:4000007"
RD = "xmet:4000008"
ISOREDOX = "xmet:4000265"
CONJUGATION = "xmet:4000011"
TRANSFER = "xmet:4000266"
ADDUCT = "xmet:4000267"
REARRANGEMENT = "xmet:4000190"
COMPOSITE = "xmet:4000272"
UNPLACED = "xmet:4000213"

# Chemist concept IDs for Forest PhaseOneRS rules (prefer non-forest-map).
# Placement follows draft-reaction-class-phase1-tree.json color grouping.
PHASEONE_IMPORT: dict[str, tuple[str, str]] = {
    # rule_name: (xmet_id, parent_id)
    "Hydroxylation": ("xmet:4000012", SO),
    "Epoxidation": ("xmet:4000022", SO),
    "NitrogenOxidation": ("xmet:4000026", SO),
    "SulfurOxidation": ("xmet:4000032", SO),
    "Dealkylation": ("xmet:4000042", UO),
    "OxidativeDehalogenation": ("xmet:4000051", UO),
    "Dehydrogenation": ("xmet:4000006", OXIDATION),  # color node itself
    "Hydrolysis": ("xmet:4000007", ISOREDOX),  # color under isoredox
    "EpoxideOpening": ("xmet:4000077", HD),
    "Dephosphorylation": ("xmet:4000087", HD),
    "Hydrogenation": ("xmet:4000090", RD),
    "NitrogenReduction": ("xmet:4000093", RD),
    "OxygenReduction": ("xmet:4000101", RD),
    "SulfurReduction": ("xmet:4000106", RD),
    "ReductiveDehalogenation": ("xmet:4000110", RD),
    "Dehydration": ("xmet:4000113", RD),  # Forest draft places under RD
}

# Extra useful children under dealkylation / colors
EXTRA_IMPORT: dict[str, str] = {
    "xmet:4000043": "xmet:4000042",  # N-dealkylation → dealkylation
    "xmet:4000044": "xmet:4000042",  # O-dealkylation
    "xmet:4000045": "xmet:4000042",  # S-dealkylation if exists
    "xmet:4000046": "xmet:4000042",  # C-dealkylation if exists
}

CONJ_IMPORT: dict[str, str] = {
    "xmet:4000148": TRANSFER,  # glucuronidation
    "xmet:4000158": TRANSFER,  # sulfation
    "xmet:4000163": TRANSFER,  # acetylation
    "xmet:4000175": TRANSFER,  # methylation
    "xmet:4000179": TRANSFER,  # amino acid conjugation
    "xmet:4000184": TRANSFER,  # glycosylation
    "xmet:4000185": TRANSFER,  # CoA
    "xmet:4000131": TRANSFER,  # formylation
    "xmet:4000167": ADDUCT,  # glutathione conjugation
    "xmet:4000268": ADDUCT,  # protein adduct
    "xmet:4000269": ADDUCT,  # DNA adduct
    "xmet:4000270": ADDUCT,  # cyanide conjugation
    "xmet:4000174": ADDUCT,  # mercapturic if present
    "xmet:4000217": ADDUCT,  # cysteine conjugation
    "xmet:4000218": ADDUCT,  # NAC
}

REARR_IMPORT: dict[str, str] = {
    "xmet:4000186": REARRANGEMENT,  # tautomerization
    "xmet:4000189": REARRANGEMENT,  # isomerization
    "xmet:4000271": REARRANGEMENT,  # skeletal
}


def concept(
    cid: str,
    label: str,
    definition: str,
    parents: list[str],
    synonyms: list[str] | None = None,
) -> dict[str, Any]:
    c: dict[str, Any] = {
        "id": cid,
        "preferred_label": label,
        "definition": definition,
        "parents": parents,
    }
    if synonyms:
        c["synonyms"] = synonyms
    return c


def set_parents(c: dict[str, Any], parents: list[str]) -> None:
    seen: set[str] = set()
    out: list[str] = []
    for p in parents:
        if p and p not in seen:
            seen.add(p)
            out.append(p)
    c["parents"] = out


def ancestors(cid: str, pm: dict[str, list[str]], memo: dict[str, set[str]] | None = None) -> set[str]:
    if memo is None:
        memo = {}
    if cid in memo:
        return memo[cid]
    out: set[str] = set()
    for p in pm.get(cid, []):
        out.add(p)
        out |= ancestors(p, pm, memo)
    memo[cid] = out
    return out


def build_parent_map(by: dict[str, dict[str, Any]]) -> dict[str, str]:
    """Return desired primary chem parent for each imported / backbone concept."""
    parent_of: dict[str, str] = {
        OXIDATION: REACTION_CLASS,
        SO: OXIDATION,
        UO: OXIDATION,
        DH: OXIDATION,
        RD: REACTION_CLASS,
        ISOREDOX: REACTION_CLASS,
        HD: ISOREDOX,
        CONJUGATION: REACTION_CLASS,
        TRANSFER: CONJUGATION,
        ADDUCT: CONJUGATION,
        REARRANGEMENT: REACTION_CLASS,
        COMPOSITE: REACTION_CLASS,
        UNPLACED: REACTION_CLASS,
    }
    for _rule, (xid, parent) in PHASEONE_IMPORT.items():
        if xid in (DH, HD):
            continue  # already set as colors
        parent_of[xid] = parent
    for xid, parent in EXTRA_IMPORT.items():
        if xid in by:
            parent_of[xid] = parent
    for xid, parent in CONJ_IMPORT.items():
        if xid in by:
            parent_of[xid] = parent
    for xid, parent in REARR_IMPORT.items():
        if xid in by:
            parent_of[xid] = parent
    return parent_of


def apply(data: dict[str, Any]) -> list[dict[str, str]]:
    remap: list[dict[str, str]] = []
    concepts = data["concepts"]
    by = {c["id"]: c for c in concepts}

    if UNPLACED not in by:
        concepts.append(
            concept(
                UNPLACED,
                "unplaced reaction class term",
                "Holding shelf for reaction-class concepts not yet re-homed under the "
                "clean oxidation / reduction / isoredox / conjugation / rearrangement "
                "skeleton. Import deliberately; do not annotate new work here.",
                parents=[REACTION_CLASS],
                synonyms=["unplaced", "reaction class parking"],
            )
        )
        by[UNPLACED] = concepts[-1]
        remap.append(
            {
                "old_id": "",
                "new_id": UNPLACED,
                "change_type": "moved",
                "note": "parking shelf for clean reaction-class rebuild",
            }
        )

    # Ensure backbone labels/defs
    by[REACTION_CLASS]["preferred_label"] = "reaction class"
    by[OXIDATION]["preferred_label"] = "oxidation"
    by[OXIDATION]["definition"] = (
        "Oxidations and related increase of oxidation state. Holds Rainbow stable "
        "oxygenation, unstable oxygenation, and dehydrogenation."
    )
    by[ISOREDOX]["preferred_label"] = "isoredox"
    by[ISOREDOX]["definition"] = (
        "Redox-neutral transformations (Rainbow sense). Holds hydrolysis and related "
        "water-mediated bond breaks."
    )
    by[RD]["preferred_label"] = "reduction"
    by[CONJUGATION]["preferred_label"] = "conjugation"
    by[TRANSFER]["preferred_label"] = "transfer conjugation"
    by[ADDUCT]["preferred_label"] = "adduct formation"

    parent_of = build_parent_map(by)

    # Current parent map
    pm = {c["id"]: list(c.get("parents") or []) for c in concepts}

    # Everyone currently under reaction-class subtree
    under_rc = [
        cid
        for cid in by
        if cid != REACTION_CLASS
        and (REACTION_CLASS in pm.get(cid, []) or REACTION_CLASS in ancestors(cid, pm))
    ]

    # Apply clean parents for backbone + imports
    for cid, parent in parent_of.items():
        if cid not in by:
            continue
        set_parents(by[cid], [parent])

    # Special: SO/UO under oxidation (already in parent_of)
    set_parents(by[SO], [OXIDATION])
    set_parents(by[UO], [OXIDATION])
    set_parents(by[DH], [OXIDATION])
    set_parents(by[HD], [ISOREDOX])
    set_parents(by[RD], [REACTION_CLASS])

    # Refresh pm after backbone
    pm = {c["id"]: list(c.get("parents") or []) for c in concepts}

    placed = set(parent_of) | {REACTION_CLASS, UNPLACED}
    # Also keep reaction-descriptor / disposition / relation out of this pass
    non_rc_spines = {
        "xmet:4000212",
        "xmet:4000263",
        "xmet:4000281",
        "xmet:4000220",
        "xmet:4000229",
        "xmet:4000000",
    }

    parked = 0
    for cid in under_rc:
        if cid in placed:
            continue
        c = by[cid]
        # Forest-map 9* alias spine: leave under forest map if that's their home
        if cid.startswith("xmet:9"):
            # strip reaction-class parent if present; keep forest-map parents
            ps = [p for p in (c.get("parents") or []) if p != REACTION_CLASS and p != UNPLACED]
            if not ps:
                # hang under forest map root if known
                ps = ["xmet:9000000"] if "xmet:9000000" in by else [UNPLACED]
            set_parents(c, ps)
            continue
        # If concept primarily lives in another spine (descriptor etc.), strip RC only
        ps = list(c.get("parents") or [])
        anc = ancestors(cid, pm)
        if any(s in anc or s in ps for s in non_rc_spines - {"xmet:4000000"}):
            set_parents(c, [p for p in ps if p != REACTION_CLASS and p not in placed])
            if not c["parents"]:
                set_parents(c, [UNPLACED])
                parked += 1
            continue
        # Default: park
        set_parents(c, [UNPLACED])
        parked += 1

    remap.append(
        {
            "old_id": "",
            "new_id": "",
            "change_type": "relabeled",
            "note": f"clean reaction-class rebuild; parked {parked} terms under {UNPLACED}",
        }
    )
    return remap


def prefer_chemist_forest_sssom() -> None:
    """For each forest.rule/pattern object, prefer non-9* chemist subject when duplicate."""
    if not FOREST_SSSOM.exists():
        return
    lines = FOREST_SSSOM.read_text().splitlines()
    comments: list[str] = []
    i = 0
    while i < len(lines) and lines[i].startswith("#"):
        comments.append(lines[i])
        i += 1
    header = lines[i]
    i += 1
    fields = header.split("\t")
    rows = [dict(zip(fields, ln.split("\t"))) for ln in lines[i:] if ln.strip()]

    by_obj: dict[str, list[dict[str, str]]] = {}
    for r in rows:
        by_obj.setdefault(r["object_id"], []).append(r)

    new_rows: list[dict[str, str]] = []
    seen_obj_chem: set[str] = set()
    for r in rows:
        obj = r["object_id"]
        group = by_obj[obj]
        chemists = [g for g in group if not g["subject_id"].startswith("xmet:9")]
        aliases = [g for g in group if g["subject_id"].startswith("xmet:9")]
        if chemists:
            # keep chemist rows; drop alias duplicates for same object
            if r["subject_id"].startswith("xmet:9") and any(
                c["subject_id"] != r["subject_id"] for c in chemists
            ):
                continue
            key = (r["subject_id"], obj)
            if key in seen_obj_chem:
                continue
            seen_obj_chem.add(f"{r['subject_id']}|{obj}")
            new_rows.append(r)
        else:
            new_rows.append(r)

    # dedupe
    out: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for r in new_rows:
        key = (r["subject_id"], r["object_id"])
        if key in seen:
            continue
        seen.add(key)
        out.append(r)

    text = comments + [header] + ["\t".join(r.get(f, "") for f in fields) for r in out]
    FOREST_SSSOM.write_text("\n".join(text) + "\n")
    print(f"forest SSSOM: {len(rows)} → {len(out)} rows (prefer chemist subjects)")


def main() -> None:
    ARTIFACTS.mkdir(exist_ok=True)
    backup = ARTIFACTS / "xmet.yaml.pre-clean-rxn-class.yaml"
    text = YAML_PATH.read_text()
    if not backup.exists():
        backup.write_text(text)
        print(f"backup → {backup}")

    data = yaml.safe_load(text)
    remap_rows = apply(data)

    YAML_PATH.write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=100)
    )

    # append remap notes
    with REMAP_PATH.open("a", newline="") as fh:
        w = csv.DictWriter(
            fh, fieldnames=["old_id", "new_id", "change_type", "note"], delimiter="\t"
        )
        for row in remap_rows:
            w.writerow(row)

    prefer_chemist_forest_sssom()

    # quick stats
    by = {c["id"]: c for c in data["concepts"]}
    direct = [
        c["preferred_label"]
        for c in data["concepts"]
        if REACTION_CLASS in (c.get("parents") or [])
    ]
    parked = sum(1 for c in data["concepts"] if UNPLACED in (c.get("parents") or []))
    print(f"reaction class direct children: {len(direct)}")
    for lab in sorted(direct):
        print(f"  - {lab}")
    print(f"parked under unplaced: {parked}")
    print(f"wrote {YAML_PATH}")


if __name__ == "__main__":
    main()
