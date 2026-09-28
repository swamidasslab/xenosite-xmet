#!/usr/bin/env python3
"""Thin/reorganize reaction-descriptor aromaticity, structural delta, mass shift.

- Consolidate aromaticity under ``aromaticity effect`` (reaction descriptor).
- Move ``mass shift`` to sibling of ``structural delta``; keep only high-signal
  drug-dev MS cues (GSH +129 NL, +305, GlcA, sulfate, cyanide, demethylation,
  oxygenation).
- Retire engine/taxonomy spray under structural delta (bond-edit, formula-delta
  class, pathway-step, redox polarity, ring fate, cardinality, oxygenation
  outcome, and flat delta peers that are not mass/aromaticity/ring).
"""

from __future__ import annotations

import csv
import io
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
    ROOT / "data/mappings/xmet-tagger.sssom.tsv",
]

RD = "xmet:4000263"
SD = "xmet:4000220"
MS = "xmet:4000221"
RING = "xmet:4000273"
PF = "xmet:0004000"  # process facet

# Restore aromaticity effect (was retired earlier as 3000510 — reuse id)
AROM = "xmet:4000274"

REF_KEYS = (
    "parents",
    "related_match",
    "close_match",
    "exact_match",
    "broad_match",
    "narrow_match",
    "partners",
    "has_part",
    "is_part_of",
)


def children_map(concepts: list[dict[str, Any]]) -> dict[str, list[str]]:
    ch: dict[str, list[str]] = defaultdict(list)
    for c in concepts:
        for p in c.get("parents") or []:
            ch[p].append(c["id"])
    return ch


def subtree_ids(root: str, ch: dict[str, list[str]]) -> set[str]:
    out: set[str] = set()
    stack = [root]
    while stack:
        cur = stack.pop()
        if cur in out:
            continue
        out.add(cur)
        stack.extend(ch.get(cur, []))
    return out


def scrub_refs(value: Any, drop: set[str]) -> Any:
    if isinstance(value, list):
        out = []
        seen: set[str] = set()
        for item in value:
            if isinstance(item, str) and item in drop:
                continue
            if isinstance(item, str):
                if item in seen:
                    continue
                seen.add(item)
            out.append(scrub_refs(item, drop))
        return out
    if isinstance(value, dict):
        return {k: scrub_refs(v, drop) for k, v in value.items()}
    return value


def append_remap(rows: list[dict[str, str]]) -> None:
    fieldnames = ["old_id", "new_id", "change_type", "note"]
    existing: list[dict[str, str]] = []
    if REMAP_PATH.exists():
        with REMAP_PATH.open() as fh:
            existing = list(csv.DictReader(fh, delimiter="\t"))
    by_old: dict[str, dict[str, str]] = {}
    for r in existing:
        oid = r.get("old_id") or ""
        if not oid:
            continue
        by_old[oid] = {
            "old_id": oid,
            "new_id": r.get("new_id", ""),
            "change_type": r.get("change_type", ""),
            "note": r.get("note") or r.get("notes") or "",
        }
    for row in rows:
        by_old[row["old_id"]] = {
            "old_id": row["old_id"],
            "new_id": row.get("new_id", ""),
            "change_type": row.get("change_type", ""),
            "note": row.get("note") or "",
        }
    with REMAP_PATH.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames, delimiter="\t", lineterminator="\n")
        w.writeheader()
        for oid in sorted(by_old):
            w.writerow({k: by_old[oid].get(k, "") for k in fieldnames})


def scrub_sssom(drop: set[str], merges: dict[str, str]) -> None:
    for path in SSSOM_PATHS:
        if not path.exists():
            continue
        text = path.read_text()
        header = [ln for ln in text.splitlines(keepends=True) if ln.startswith("#")]
        body = [ln for ln in text.splitlines(keepends=True) if not ln.startswith("#")]
        rows = list(csv.DictReader(io.StringIO("".join(body)), delimiter="\t"))
        if not rows:
            continue
        fields = list(rows[0].keys())
        kept = []
        seen: set[tuple[str, str, str]] = set()
        for r in rows:
            sub = r.get("subject_id") or ""
            if sub in drop:
                continue
            if sub in merges:
                r = dict(r)
                r["subject_id"] = merges[sub]
            key = (r.get("subject_id", ""), r.get("predicate_id", ""), r.get("object_id", ""))
            if key in seen:
                continue
            seen.add(key)
            kept.append(r)
        with path.open("w", newline="") as fh:
            fh.writelines(header)
            w = csv.DictWriter(fh, fieldnames=fields, delimiter="\t", lineterminator="\n")
            w.writeheader()
            w.writerows(kept)


def main() -> int:
    data = yaml.safe_load(YAML_PATH.read_text())
    concepts: list[dict[str, Any]] = data["concepts"]
    by = {c["id"]: c for c in concepts}
    labels = {c["id"]: c.get("preferred_label") or c["id"] for c in concepts}
    ch = children_map(concepts)

    # --- 1) aromaticity effect shelf ---
    if AROM not in by:
        arom = {
            "id": AROM,
            "preferred_label": "aromaticity effect",
            "definition": (
                "Gain or loss of aromatic character accompanying a transformation "
                "(aromatization / rearomatization / dearomatization)."
            ),
            "synonyms": ["aromaticity change", "aromaticity descriptor"],
            "parents": [RD],
        }
        concepts.append(arom)
        by[AROM] = arom
        print(f"mint {AROM} aromaticity effect")
    else:
        by[AROM]["parents"] = [RD]
        by[AROM]["preferred_label"] = "aromaticity effect"
        by[AROM]["definition"] = (
            "Gain or loss of aromatic character accompanying a transformation "
            "(aromatization / rearomatization / dearomatization)."
        )

    # Move dearomatization / rearomatization under aromaticity effect
    by["xmet:4000194"]["parents"] = [AROM]
    by["xmet:4000195"]["parents"] = [AROM]
    # aromatization stays under rearomatization
    # thiophene S-oxidation: chemistry parent only (drop dearomatization parent)
    tso = by["xmet:4000035"]
    tso["parents"] = [p for p in (tso.get("parents") or []) if p != "xmet:4000194"]
    if "xmet:4000032" not in tso["parents"]:
        tso["parents"].insert(0, "xmet:4000032")
    rm = list(tso.get("related_match") or [])
    if "xmet:4000194" not in rm:
        rm.append("xmet:4000194")
    tso["related_match"] = rm

    # Merge flat aromaticity deltas into aromaticity effect (retire)
    merges: dict[str, str] = {
        "xmet:4000274": AROM,  # aromaticity change
        "xmet:4000194": "xmet:4000194",  # loss → dearomatization
        "xmet:4000195": "xmet:4000195",  # gain → rearomatization
    }

    # --- 2) mass shift: sibling of structural delta under RD ---
    by[MS]["parents"] = [RD]
    by[MS]["definition"] = (
        "High-signal MS mass difference or neutral-loss cues used in drug-metabolism "
        "structure elucidation (not a dump of all formula deltas)."
    )

    # Nest / relabel keepers under mass shift
    keep_ms = {
        "xmet:4000228": (  # GSH mass shift
            MS,
            "GSH mass shift",
            "Nominal +305 Da (glutathione conjugation / adduct). Suggests glutathionation.",
            ["+305 Da", "glutathione mass shift"],
        ),
        "xmet:4000279": (  # NL 129
            "xmet:4000228",
            "GSH pyroglutamate neutral loss",
            "Characteristic MS neutral loss of ~129 Da (pyroglutamate) suggesting "
            "glutathione conjugation / GSH adduct.",
            ["129 Da neutral loss", "pyroglutamate neutral loss"],
        ),
        "xmet:4000226": (
            MS,
            "glucuronide mass shift",
            "Nominal +176 Da for glucuronide conjugation. Suggests glucuronidation.",
            ["+176 Da", "GlcA mass shift"],
        ),
        "xmet:4000227": (
            MS,
            "sulfate mass shift",
            "Nominal +80 Da for sulfate conjugation. Suggests sulfation.",
            ["+80 Da", "sulfate conjugation mass shift"],
        ),
        "xmet:4000280": (
            MS,
            "cyanide mass shift",
            "Mass cue / neutral loss of ~27 Da (HCN) suggesting cyanide conjugation / trapping.",
            ["~27 Da", "HCN neutral loss", "cyanide neutral loss"],
        ),
        "xmet:4000224": (
            MS,
            "demethylation mass shift",
            "Nominal −14 Da (loss of CH₂). Suggests N-/O-/S-demethylation.",
            ["−14 Da", "demethylation delta"],
        ),
        "xmet:4000225": (
            MS,
            "deethylation mass shift",
            "Nominal −28 Da (loss of C₂H₄). Suggests N-/O-deethylation.",
            ["−28 Da", "deethylation delta"],
        ),
        "xmet:4000223": (
            MS,
            "oxygenation mass shift",
            "Nominal +16 Da (monooxygenation). Suggests hydroxylation / other +O paths; "
            "+32 Da dioxygenation is related.",
            ["+16 Da", "monooxygenation", "oxygen gain mass shift"],
        ),
    }
    for cid, (parent, lab, defn, syns) in keep_ms.items():
        c = by[cid]
        c["parents"] = [parent]
        c["preferred_label"] = lab
        c["definition"] = defn
        c["synonyms"] = list(dict.fromkeys([*(c.get("synonyms") or []), *syns]))

    merges["xmet:4000223"] = "xmet:4000223"  # dioxygenation → oxygenation mass shift

    # suggests soft links on mass shifts (related_match to chemistry)
    suggests = {
        "xmet:4000228": ["xmet:4000167"],  # GSH → glutathione conjugation
        "xmet:4000279": ["xmet:4000167"],
        "xmet:4000226": ["xmet:4000148"],
        "xmet:4000227": ["xmet:4000158"],
        "xmet:4000280": ["xmet:4000270"] if "xmet:4000270" in by else ["xmet:4000114"],
        "xmet:4000224": ["xmet:4000349", "xmet:4000042"],
        "xmet:4000225": ["xmet:4000042"],
        "xmet:4000223": ["xmet:4000012", "xmet:4000004"],
    }
    for cid, targets in suggests.items():
        rm = [t for t in targets if t in by]
        existing = [x for x in (by[cid].get("related_match") or []) if x in by or x.startswith("xmet:")]
        by[cid]["related_match"] = list(dict.fromkeys(rm + existing))

    # --- 3) ring expansion/contraction deltas → ring effect ---
    if "xmet:4000201" in by:
        by["xmet:4000201"]["parents"] = [RING]
        by["xmet:4000201"]["preferred_label"] = "ring expansion"
        # avoid clash if ring expansion already exists under skeletal
    if "xmet:4000202" in by:
        by["xmet:4000202"]["parents"] = [RING]
        by["xmet:4000202"]["preferred_label"] = "ring contraction"

    # --- 4) structural delta: keep only stereochemical change (medchem discourse) ---
    keep_under_sd = {"xmet:4000222"}  # stereochemical change
    if "xmet:4000222" in by:
        by["xmet:4000222"]["parents"] = [SD]
        by[SD]["definition"] = (
            "Thin shelf for structural-edit descriptors common in med-chem discourse "
            "(not engine topology / formula-delta taxonomies). Mass cues live under "
            "mass shift; aromaticity under aromaticity effect; ring under ring effect."
        )

    # Engine shelves + leftover flat peers to retire (whole subtrees)
    engine_roots = [
        "xmet:7000000",
        "xmet:7200000",
        "xmet:7300000",
        "xmet:7400000",
        "xmet:7600000",
        "xmet:7700000",
        "xmet:7900000",
    ]
    # refresh children after edits
    ch = children_map(concepts)
    drop: set[str] = set()
    for root in engine_roots:
        if root in by:
            drop |= subtree_ids(root, ch)

    # Flat SD peers not kept / not moved to MS / ring / arom
    ch = children_map(concepts)
    for cid in list(ch.get(SD, [])):
        if cid in (MS, *keep_under_sd, "xmet:4000201", "xmet:4000202"):
            continue
        if cid in keep_ms or cid in merges:
            continue
        # still parented under SD?
        if SD in (by[cid].get("parents") or []):
            drop.add(cid)

    # Also drop aromaticity delta ids via merge (not hard-drop without merge target)
    for old in merges:
        drop.add(old)

    # process facet: retire if only empty shelf after arom move
    ch = children_map(concepts)
    # update dearomatization parents already set; process facet kids?
    pf_kids = [
        k
        for k in ch.get(PF, [])
        if k not in drop and k in by and PF in (by[k].get("parents") or [])
    ]
    # After arom move, dearomatization/rearomatization no longer under PF
    # Any remaining PF kids?
    still_pf = []
    for c in concepts:
        if PF in (c.get("parents") or []) and c["id"] not in drop:
            still_pf.append(c["id"])
    if not still_pf:
        drop.add(PF)
        print("retire empty process facet")
    else:
        print("process facet still has", still_pf)

    # Don't drop kept mass-shift / arom / ring-moved / SD-kept
    protect = {
        SD,
        RD,
        MS,
        AROM,
        RING,
        "xmet:4000194",
        "xmet:4000195",
        "xmet:4000074",
        *keep_ms.keys(),
        *keep_under_sd,
        "xmet:4000201",
        "xmet:4000202",
    }
    drop -= protect
    # merge targets stay
    drop -= set(merges.values())

    print(f"retiring {len(drop)} concepts")

    remap_rows = []
    for old, new in merges.items():
        remap_rows.append(
            {
                "old_id": old,
                "new_id": new,
                "change_type": "merged",
                "note": f"{labels.get(old, old)} merged into {labels.get(new, new)} / aromaticity-mass thin",
            }
        )
    for cid in sorted(drop):
        if cid in merges:
            continue
        remap_rows.append(
            {
                "old_id": cid,
                "new_id": "",
                "change_type": "retired",
                "note": f"retired {labels.get(cid, cid)} (thin structural delta / descriptor cleanup)",
            }
        )

    # Apply merges in refs before drop
    for c in concepts:
        for key in REF_KEYS:
            if key not in c:
                continue
            vals = []
            seen: set[str] = set()
            for v in c[key] or []:
                if isinstance(v, str) and v in merges:
                    v = merges[v]
                if isinstance(v, str):
                    if v in seen:
                        continue
                    seen.add(v)
                vals.append(v)
            c[key] = vals

    for c in concepts:
        for key in REF_KEYS:
            if key in c:
                c[key] = scrub_refs(c[key], drop)
                if not c[key]:
                    del c[key]

    data["concepts"] = [c for c in concepts if c["id"] not in drop]

    # Final scrub dangling
    live = {c["id"] for c in data["concepts"]}
    for c in data["concepts"]:
        for key in REF_KEYS:
            if key not in c:
                continue
            c[key] = [v for v in c[key] if not (isinstance(v, str) and v.startswith("xmet:") and v not in live)]
            if not c[key]:
                del c[key]

    YAML_PATH.write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=100, default_flow_style=False)
    )
    append_remap(remap_rows)
    scrub_sssom(drop, merges)

    # Report
    by = {c["id"]: c for c in data["concepts"]}
    ch = children_map(data["concepts"])
    print("\nreaction descriptor children:")
    for cid in sorted(ch[RD], key=lambda i: by[i]["preferred_label"].lower()):
        print(f"  {by[cid]['preferred_label']} ({len(ch[cid])} kids)")
    print("\naromaticity effect:")
    for cid in sorted(ch.get(AROM, []), key=lambda i: by[i]["preferred_label"].lower()):
        print(f"  {by[cid]['preferred_label']}")
    print("\nmass shift:")
    for cid in sorted(ch.get(MS, []), key=lambda i: by[i]["preferred_label"].lower()):
        print(f"  {by[cid]['preferred_label']} ({len(ch[cid])} kids)")
        for k in sorted(ch.get(cid, []), key=lambda i: by[i]["preferred_label"].lower()):
            print(f"    {by[k]['preferred_label']}")
    print("\nstructural delta:")
    for cid in sorted(ch.get(SD, []), key=lambda i: by[i]["preferred_label"].lower()):
        print(f"  {by[cid]['preferred_label']}")
    print(f"\nconcepts now {len(data['concepts'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
