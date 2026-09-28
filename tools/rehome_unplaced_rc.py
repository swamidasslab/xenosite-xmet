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

UNPLACED = "xmet:3000990"

# old_id → surviving id (retire old)
MERGES: dict[str, str] = {
    "xmet:1100013": "xmet:0000208",  # deamination → oxidative deamination
    "xmet:0000021": "xmet:0000020",  # carbon oxidation → oxidation
    "xmet:0000023": "xmet:0000200",  # C–X oxidative cleavage → dealkylation
}

# id → new parents (replaces unplaced parent; preserves other non-unplaced parents)
PLACES: dict[str, list[str]] = {
    "xmet:0000022": ["xmet:0000010"],  # heteroatom oxidation → SO
    "xmet:1100016": ["xmet:0000020"],  # ring oxidation
    "xmet:0000610": ["xmet:3000005"],  # alkylation → isoredox
    "xmet:0000611": ["xmet:0000610"],
    "xmet:0000612": ["xmet:0000610"],
    "xmet:0000613": ["xmet:0000610"],
    "xmet:0000614": ["xmet:0000610"],
    "xmet:0000661": ["xmet:3000005"],  # amination
    "xmet:0000730": ["xmet:3000005"],  # arylation
    "xmet:0000621": ["xmet:3000005"],  # carboxylation
    "xmet:0000620": ["xmet:3000005"],  # decarboxylation
    "xmet:0000731": ["xmet:3000005"],  # carbonylation
    "xmet:0002007": ["xmet:3000005"],  # decarbonylation
    "xmet:0000660": ["xmet:3000005"],  # halogenation
    "xmet:0000650": ["xmet:3000005"],  # dehydroxylation
    "xmet:0000691": ["xmet:3000005"],  # sulfuration
    "xmet:0000630": ["xmet:3000005"],  # esterification
    "xmet:0000631": ["xmet:0000630"],  # transesterification
    "xmet:0000640": ["xmet:3000300"],  # cyclization → skeletal rearrangement
    "xmet:0000632": ["xmet:0000640"],  # lactonization
    "xmet:0000633": ["xmet:0000640"],  # lactamization
    "xmet:0000412": ["xmet:0000510"],  # azo cleavage → nitrogen reduction
    "xmet:0004006": ["xmet:3001146"],  # carbinolamine → hemiaminal collapse
    "xmet:0004007": ["xmet:0000202"],  # hemiacetal → O-dealkylation
    "xmet:0004011": ["xmet:0000100"],  # cis-dihydroxylation → hydroxylation
    "xmet:0004014": ["xmet:3000200"],  # conjugate addition → adduct
    "xmet:0000600": ["xmet:3000200"],  # cyanidation
    "xmet:0000601": ["xmet:3001111"],  # decyanidation → hydrolytic cleavage
    "xmet:0001023": ["xmet:3001111"],  # deacetylation
    "xmet:0002005": ["xmet:3001111"],  # deacylation
    "xmet:0000671": ["xmet:3001111"],  # deformylation
    "xmet:0000732": ["xmet:0000024"],  # deconjugation → conjugation
    "xmet:0000700": ["xmet:0000732"],
    "xmet:0000701": ["xmet:0000732"],
    "xmet:0000702": ["xmet:0000732"],
    "xmet:0000703": ["xmet:0000732"],
    "xmet:0000704": ["xmet:0000732"],
    "xmet:1100014": ["xmet:1100000"],  # dehalogenation umbrella
    "xmet:0002006": ["xmet:3000300"],  # denitrogenation
    "xmet:0000680": ["xmet:0000120"],  # N-nitrosation → nitrogen oxidation
    "xmet:0000681": ["xmet:0000510"],  # denitrosation → nitrogen reduction
    "xmet:0000690": ["xmet:0000130"],  # desulfuration → sulfur oxidation
    "xmet:0000710": ["xmet:0001040"],  # Se-methylation → methylation
    "xmet:0004004": ["xmet:0000101"],  # ipso → aromatic hydroxylation
    "xmet:0004015": ["xmet:3000200"],  # SNAr → adduct
    "xmet:0004017": ["xmet:0002004"],  # acyl migration → rearrangement
    "xmet:0004018": ["xmet:3000100"],  # transacylation → transfer
    "xmet:0004009": ["xmet:3000300"],
    "xmet:0004010": ["xmet:3000300"],
    "xmet:0004016": ["xmet:3000300"],
    "xmet:0004019": ["xmet:3000300"],
    "xmet:0000307": ["xmet:0000300"],
    "xmet:0000308": ["xmet:0000300"],
    "xmet:0000309": ["xmet:0000300"],
    "xmet:0004000": ["xmet:3000000"],  # process facet → reaction descriptor
}

# After placing heteroatom oxidation: N/S oxidation parent SO → heteroatom oxidation
REPARENT_UNDER_HETEROATOM = ("xmet:0000120", "xmet:0000130")

# Add dehalogenation as extra parent (keep color parents)
DEHALOGENATION_CHILDREN = ("xmet:0000210", "xmet:0000540")


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
        parents = [p for p in (c.get("parents") or []) if p != "xmet:0000010"]
        if "xmet:0000022" not in parents:
            parents.insert(0, "xmet:0000022")
        c["parents"] = parents
        print(f"nest {cid} {labels[cid]} under heteroatom oxidation → {parents}")

    # 3) dehalogenation umbrella
    for cid in DEHALOGENATION_CHILDREN:
        c = by[cid]
        parents = list(c.get("parents") or [])
        if "xmet:1100014" not in parents:
            parents.append("xmet:1100014")
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
                "new_id": "xmet:1100000",
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
