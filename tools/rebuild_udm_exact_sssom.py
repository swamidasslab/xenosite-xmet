#!/usr/bin/env python3
"""Rebuild high-confidence UDM/MOP exactMatch SSSOM rows.

Criteria (all required):
  - XMET preferred_label appears as a UDM 6.0.0 reactionClass enumeration
  - mop.obo has that exact name → unique ID (do not trust UDM XSD comments)
  - XMET definition states the same chemistry as the MOP definition (hand review)

Source: https://github.com/PistoiaAlliance/UDM/blob/master/udm_6_0_0_reaction_classes.xsd
"""

from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Hand-reviewed KEEP set (label + definition identity). Update only after review.
KEEP: dict[str, str] = {
    "xmet:4000022": "mop:0000671",  # epoxidation
    "xmet:4000214": "mop:0001550",  # dehalogenation
    "xmet:4000116": "mop:0000369",  # alkylation
    "xmet:4000117": "mop:0002369",  # N-alkylation
    "xmet:4000122": "mop:0000591",  # carboxylation
    "xmet:4000127": "mop:0000561",  # cyclization
    "xmet:4000129": "mop:0000550",  # halogenation
    "xmet:4000130": "mop:0000650",  # amination
    "xmet:4000131": "mop:0000003",  # formylation
    "xmet:4000145": "mop:0000411",  # arylation
}

FIELDS = [
    "subject_id",
    "predicate_id",
    "object_id",
    "mapping_justification",
    "subject_label",
    "object_label",
]


def main() -> None:
    import yaml

    data = yaml.safe_load((ROOT / "data/ontology/xmet.yaml").read_text())
    by = {c["id"]: c for c in data["concepts"]}
    rows = []
    for cid, obj in KEEP.items():
        c = by[cid]
        rows.append(
            {
                "subject_id": cid,
                "predicate_id": "skos:exactMatch",
                "object_id": obj,
                "mapping_justification": "semapv:ManualMappingCuration",
                "subject_label": c["preferred_label"],
                "object_label": c["preferred_label"],
            }
        )

    udm_path = ROOT / "data/mappings/xmet-udm.sssom.tsv"
    with udm_path.open("w", newline="") as fh:
        fh.write("# High-confidence exactMatch only (label + definition review).\n")
        fh.write("# UDM: https://github.com/PistoiaAlliance/UDM udm_6_0_0_reaction_classes.xsd\n")
        fh.write("# object_id from mop.obo name lookup (UDM XML comments not trusted).\n")
        w = csv.DictWriter(fh, fieldnames=FIELDS, delimiter="\t")
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print(f"wrote {udm_path} ({len(rows)} rows)")


if __name__ == "__main__":
    main()
