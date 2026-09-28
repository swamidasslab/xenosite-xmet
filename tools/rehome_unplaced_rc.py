#!/usr/bin/env python3
"""Rehome unplaced reaction-class terms; merge true duplicates.

- Place antonyms / specializations under existing chemist parents.
- Merge label/chemistry duplicates into the live Forest-aligned concept.
- Insert heteroatom oxidation under stable oxygenation (parent of N/S oxidation).
- Add dehalogenation as umbrella parent of oxidative + reductive dehalogenation.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
YAML_PATH = ROOT / "data/ontology/xmet.yaml"
REMAP_PATH = ROOT / "data/mappings/xmet-id-remap.tsv"

UNPLACED = "xmet:4000213"

# old_id → surviving id (retire old)
MERGES: dict[str, str] = {
    "xmet:4000049": "xmet:4000049",  # deamination → oxidative deamination
    "xmet:4000009": "xmet:4000009",  # carbon oxidation → oxidation
    "xmet:4000042": "xmet:4000042",  # C–X oxidative cleavage → dealkylation
}

# id → new parents (replaces unplaced parent; preserves other non-unplaced parents)
PLACES: dict[str, list[str]] = {
    "xmet:4000010": ["xmet:4000004"],  # heteroatom oxidation → SO
    "xmet:1100016": ["xmet:4000009"],  # ring oxidation
    "xmet:4000116": ["xmet:4000265"],  # alkylation → isoredox
    "xmet:4000117": ["xmet:4000116"],
    "xmet:4000118": ["xmet:4000116"],
    "xmet:4000119": ["xmet:4000116"],
    "xmet:4000120": ["xmet:4000116"],
    "xmet:4000130": ["xmet:4000265"],  # amination
    "xmet:4000145": ["xmet:4000265"],  # arylation
    "xmet:4000122": ["xmet:4000265"],  # carboxylation
    "xmet:4000121": ["xmet:4000265"],  # decarboxylation
    "xmet:4000146": ["xmet:4000265"],  # carbonylation
    "xmet:4000193": ["xmet:4000265"],  # decarbonylation
    "xmet:4000129": ["xmet:4000265"],  # halogenation
    "xmet:4000128": ["xmet:4000265"],  # dehydroxylation
    "xmet:4000136": ["xmet:4000265"],  # sulfuration
    "xmet:4000123": ["xmet:4000265"],  # esterification
    "xmet:4000124": ["xmet:4000123"],  # transesterification
    "xmet:4000127": ["xmet:4000271"],  # cyclization → skeletal rearrangement
    "xmet:4000125": ["xmet:4000127"],  # lactonization
    "xmet:4000126": ["xmet:4000127"],  # lactamization
    "xmet:4000089": ["xmet:4000093"],  # azo cleavage → nitrogen reduction
    "xmet:4000198": ["xmet:4000318"],  # carbinolamine → hemiaminal collapse
    "xmet:4000199": ["xmet:4000044"],  # hemiacetal → O-dealkylation
    "xmet:4000203": ["xmet:4000012"],  # cis-dihydroxylation → hydroxylation
    "xmet:4000206": ["xmet:4000267"],  # conjugate addition → adduct
    "xmet:4000114": ["xmet:4000267"],  # cyanidation
    "xmet:4000115": ["xmet:4000293"],  # decyanidation → hydrolytic cleavage
    "xmet:4000166": ["xmet:4000293"],  # deacetylation
    "xmet:4000191": ["xmet:4000293"],  # deacylation
    "xmet:4000132": ["xmet:4000293"],  # deformylation
    "xmet:4000147": ["xmet:4000011"],  # deconjugation → conjugation
    "xmet:4000137": ["xmet:4000147"],
    "xmet:4000138": ["xmet:4000147"],
    "xmet:4000139": ["xmet:4000147"],
    "xmet:4000140": ["xmet:4000147"],
    "xmet:4000141": ["xmet:4000147"],
    "xmet:4000214": ["xmet:4000213"],  # dehalogenation umbrella
    "xmet:4000192": ["xmet:4000271"],  # denitrogenation
    "xmet:4000133": ["xmet:4000026"],  # N-nitrosation → nitrogen oxidation
    "xmet:4000134": ["xmet:4000093"],  # denitrosation → nitrogen reduction
    "xmet:4000135": ["xmet:4000032"],  # desulfuration → sulfur oxidation
    "xmet:4000142": ["xmet:4000175"],  # Se-methylation → methylation
    "xmet:4000196": ["xmet:4000013"],  # ipso → aromatic hydroxylation
    "xmet:4000207": ["xmet:4000267"],  # SNAr → adduct
    "xmet:4000209": ["xmet:4000190"],  # acyl migration → rearrangement
    "xmet:4000210": ["xmet:4000266"],  # transacylation → transfer
    "xmet:4000201": ["xmet:4000271"],
    "xmet:4000202": ["xmet:4000271"],
    "xmet:4000208": ["xmet:4000271"],
    "xmet:4000211": ["xmet:4000271"],
    "xmet:4000066": ["xmet:4000059"],
    "xmet:4000067": ["xmet:4000059"],
    "xmet:4000068": ["xmet:4000059"],
    "xmet:0004000": ["xmet:4000263"],  # process facet → reaction descriptor
}

# After placing heteroatom oxidation: N/S oxidation parent SO → heteroatom oxidation
REPARENT_UNDER_HETEROATOM = ("xmet:4000026", "xmet:4000032")

# Add dehalogenation as extra parent (keep color parents)
DEHALOGENATION_CHILDREN = ("xmet:4000051", "xmet:4000110")


def rewrite_id(value: Any, merges: dict[str, str]) -> Any:
    if isinstance(value, str):
        return merges.get(value, value)
    if isinstance(value, list):
        out = []
        seen: set[str] = set()
        for item in value:
            new = rewrite_id(item, merges)
            if isinstance(new, str):
                if new in seen:
                    continue
                seen.add(new)
            out.append(new)
        return out
    if isinstance(value, dict):
        return {k: rewrite_id(v, merges) for k, v in value.items()}
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
            "note": row.get("note") or row.get("notes") or "",
        }
    with REMAP_PATH.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames, delimiter="\t", lineterminator="\n")
        w.writeheader()
        for old in sorted(by_old):
            w.writerow({k: by_old[old].get(k, "") for k in fieldnames})


def topo_place_order(places: dict[str, list[str]]) -> list[str]:
    """Parents that are themselves being placed come first."""
    pending = set(places)
    done: list[str] = []
    while pending:
        ready = [
            cid
            for cid in sorted(pending)
            if all(p not in pending for p in places[cid])
        ]
        if not ready:
            raise SystemExit(f"cycle in place parents among {sorted(pending)}")
        done.extend(ready)
        pending -= set(ready)
    return done


def main() -> int:
    data = yaml.safe_load(YAML_PATH.read_text())
    concepts: list[dict[str, Any]] = data["concepts"]
    by = {c["id"]: c for c in concepts}
    labels = {c["id"]: c.get("preferred_label") or c["id"] for c in concepts}

    unplaced_ids = {
        c["id"] for c in concepts if UNPLACED in (c.get("parents") or [])
    }
    planned = set(PLACES) | set(MERGES)
    missing = unplaced_ids - planned
    if missing:
        raise SystemExit(f"unplaced not in plan: {sorted(missing)}")
    extra = planned - unplaced_ids
    if extra:
        raise SystemExit(f"plan ids not currently unplaced: {sorted(extra)}")

    for target in MERGES.values():
        if target not in by:
            raise SystemExit(f"merge target missing: {target}")
    for cid, parents in PLACES.items():
        for p in parents:
            if p not in by and p not in PLACES:
                raise SystemExit(f"place parent missing: {p} for {cid}")

    # 1) Apply places in topological order
    for cid in topo_place_order(PLACES):
        c = by[cid]
        old_parents = list(c.get("parents") or [])
        kept = [p for p in old_parents if p != UNPLACED and p not in MERGES]
        new_parents = list(dict.fromkeys(PLACES[cid] + kept))
        c["parents"] = new_parents
        print(f"place {cid} {labels[cid]} → {new_parents}")

    # 2) heteroatom oxidation nests N/S oxidation
    for cid in REPARENT_UNDER_HETEROATOM:
        c = by[cid]
        parents = [p for p in (c.get("parents") or []) if p != "xmet:4000004"]
        if "xmet:4000010" not in parents:
            parents.insert(0, "xmet:4000010")
        c["parents"] = parents
        print(f"nest {cid} {labels[cid]} under heteroatom oxidation → {parents}")

    # 3) dehalogenation umbrella
    for cid in DEHALOGENATION_CHILDREN:
        c = by[cid]
        parents = list(c.get("parents") or [])
        if "xmet:4000214" not in parents:
            parents.append("xmet:4000214")
        c["parents"] = parents
        print(f"umbrella {cid} {labels[cid]} += dehalogenation → {parents}")

    # 4) Merges: drop retired concepts, rewrite references, remap rows
    remap_rows = []
    for old, new in MERGES.items():
        old_lab = labels[old]
        new_lab = labels[new]
        syn = list(by[new].get("synonyms") or [])
        if old_lab not in syn and old_lab != new_lab:
            syn.append(old_lab)
            by[new]["synonyms"] = syn
        remap_rows.append(
            {
                "old_id": old,
                "new_id": new,
                "change_type": "merged",
                "note": f"{old_lab} merged into {new_lab}",
            }
        )
        print(f"merge {old} {old_lab} → {new} {new_lab}")

    data["concepts"] = [c for c in data["concepts"] if c["id"] not in MERGES]

    ref_keys = (
        "parents",
        "related_match",
        "close_match",
        "exact_match",
        "broad_match",
        "narrow_match",
        "partners",
    )
    for c in data["concepts"]:
        for key in ref_keys:
            if key in c:
                c[key] = rewrite_id(c[key], MERGES)

    by = {c["id"]: c for c in data["concepts"]}
    labels = {c["id"]: c.get("preferred_label") or c["id"] for c in data["concepts"]}

    # Scrub SSSOM subjects that were merged
    for path in (
        ROOT / "data/mappings/xmet-forest.sssom.tsv",
        ROOT / "data/mappings/xmet-external.sssom.tsv",
        ROOT / "data/mappings/xmet-mop.sssom.tsv",
        ROOT / "data/mappings/xmet-mesh.sssom.tsv",
        ROOT / "data/mappings/xmet-udm.sssom.tsv",
        ROOT / "data/mappings/xmet-tagger.sssom.tsv",
    ):
        if not path.exists():
            continue
        text = path.read_text()
        header = [ln for ln in text.splitlines(keepends=True) if ln.startswith("#")]
        body = [ln for ln in text.splitlines(keepends=True) if not ln.startswith("#")]
        import io

        rows = list(csv.DictReader(io.StringIO("".join(body)), delimiter="\t"))
        if not rows:
            continue
        fields = list(rows[0].keys())
        new_rows = []
        for r in rows:
            sub = r.get("subject_id") or ""
            if sub in MERGES:
                r = dict(r)
                r["subject_id"] = MERGES[sub]
                r["subject_label"] = labels.get(MERGES[sub], r.get("subject_label", ""))
            if (r.get("subject_id") or "") in MERGES:
                continue
            new_rows.append(r)
        # dedupe subject+predicate+object
        seen: set[tuple[str, str, str]] = set()
        deduped = []
        for r in new_rows:
            key = (r.get("subject_id", ""), r.get("predicate_id", ""), r.get("object_id", ""))
            if key in seen:
                continue
            seen.add(key)
            deduped.append(r)
        with path.open("w", newline="") as fh:
            fh.writelines(header)
            w = csv.DictWriter(fh, fieldnames=fields, delimiter="\t", lineterminator="\n")
            w.writeheader()
            w.writerows(deduped)
        print(f"scrubbed SSSOM {path.name}: {len(rows)} → {len(deduped)}")

    # 5) Drop empty unplaced shelf if unused
    still = [c for c in data["concepts"] if UNPLACED in (c.get("parents") or [])]
    if still:
        print(f"WARNING: {len(still)} still under unplaced:")
        for c in still:
            print(f"  {c['id']} {c.get('preferred_label')}")
    elif UNPLACED in by:
        data["concepts"] = [c for c in data["concepts"] if c["id"] != UNPLACED]
        remap_rows.append(
            {
                "old_id": UNPLACED,
                "new_id": "xmet:4000213",
                "change_type": "retired",
                "note": "empty unplaced reaction-class shelf after rehome",
            }
        )
        print(f"retire empty {UNPLACED}")

    YAML_PATH.write_text(
        yaml.safe_dump(
            data,
            sort_keys=False,
            allow_unicode=True,
            width=100,
            default_flow_style=False,
        )
    )
    if remap_rows:
        append_remap(remap_rows)
    print(f"wrote {YAML_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
