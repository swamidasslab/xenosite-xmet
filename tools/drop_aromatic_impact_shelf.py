#!/usr/bin/env python3
"""Rehome chemist terms off deferred 8xxxxx impact shelf; delete the shelf.

Also delete empty duplicate ``aromaticity effect`` descriptor (covered by
structural-delta aromaticity terms + process-facet dearomatization/rearomatization).
"""

from __future__ import annotations

import csv
import io
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

# Deferred aromatic/conjugated impact shelf (under structural delta)
DROP = {
    "xmet:8000000",
    "xmet:8000001",
    "xmet:8000002",
    "xmet:8000003",
    "xmet:8000004",
    "xmet:8000005",
    "xmet:8000006",
    "xmet:8000007",
    "xmet:8000008",
    "xmet:4000274",  # empty aromaticity effect; duplicate of delta + process facet
}

# Chemist rehomes (replace parents entirely with these; drop 8xxxxx)
REHOME: dict[str, list[str]] = {
    "xmet:4000025": ["xmet:4000022"],  # thiophene epoxidation → epoxidation
    "xmet:4000035": ["xmet:4000032", "xmet:4000194"],  # thiophene S-ox → S-ox + dearomatization
    "xmet:4000194": ["xmet:0004000"],  # dearomatization → process facet only
    "xmet:4000195": ["xmet:0004000"],  # rearomatization
    "xmet:4000197": ["xmet:4000024", "xmet:0004000"],  # NIH shift → arene oxide + process facet
    "xmet:4000197": ["xmet:4000024", "xmet:0004000"],  # arene oxide rearrangement
}

REF_KEYS = (
    "parents",
    "related_match",
    "close_match",
    "exact_match",
    "broad_match",
    "narrow_match",
    "partners",
)


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
            if existing:
                # normalize to canonical 4 columns
                pass
    by_old = {}
    for r in existing:
        by_old[r.get("old_id", "")] = {
            "old_id": r.get("old_id", ""),
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
            if not old:
                continue
            w.writerow({k: by_old[old].get(k, "") for k in fieldnames})


def scrub_sssom(drop: set[str]) -> None:
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
        kept = [r for r in rows if (r.get("subject_id") or "") not in drop]
        if len(kept) == len(rows):
            continue
        with path.open("w", newline="") as fh:
            fh.writelines(header)
            w = csv.DictWriter(fh, fieldnames=fields, delimiter="\t", lineterminator="\n")
            w.writeheader()
            w.writerows(kept)
        print(f"scrubbed {path.name}: {len(rows)} → {len(kept)}")


def main() -> int:
    data = yaml.safe_load(YAML_PATH.read_text())
    concepts: list[dict[str, Any]] = data["concepts"]
    by = {c["id"]: c for c in concepts}
    labels = {c["id"]: c.get("preferred_label") or c["id"] for c in concepts}

    for cid, parents in REHOME.items():
        if cid not in by:
            raise SystemExit(f"missing rehome subject {cid}")
        for p in parents:
            if p not in by and p not in REHOME:
                raise SystemExit(f"missing rehome parent {p} for {cid}")
        by[cid]["parents"] = list(parents)
        print(f"rehome {cid} {labels[cid]} → {parents}")

    remap_rows = []
    for cid in sorted(DROP):
        if cid not in by:
            print(f"skip missing drop {cid}")
            continue
        remap_rows.append(
            {
                "old_id": cid,
                "new_id": "",
                "change_type": "retired",
                "note": f"retired {labels[cid]} (deferred aromatic impact shelf or empty aromaticity effect)",
            }
        )
        print(f"drop {cid} {labels[cid]}")

    for c in concepts:
        for key in REF_KEYS:
            if key in c:
                c[key] = scrub_refs(c[key], DROP)

    data["concepts"] = [c for c in concepts if c["id"] not in DROP]
    YAML_PATH.write_text(
        yaml.safe_dump(
            data,
            sort_keys=False,
            allow_unicode=True,
            width=100,
            default_flow_style=False,
        )
    )
    append_remap(remap_rows)
    scrub_sssom(DROP)

    # dangling related_match to wiped ids is pre-existing debt; scrub only DROP targets here
    live = {c["id"] for c in data["concepts"]}
    drop_dangling = [(c["id"], key, v) for c in data["concepts"] for key in REF_KEYS for v in (c.get(key) or []) if isinstance(v, str) and v in DROP]
    if drop_dangling:
        print("ERROR still referencing dropped ids:", drop_dangling[:20])
        return 1

    print(f"wrote {YAML_PATH.relative_to(ROOT)}; concepts now {len(data['concepts'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
