#!/usr/bin/env python3
"""Build matchable XMET label index from xmet.yaml."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib_match import concept_index, load_ontology, normalize_label, write_tsv  # noqa: E402


def main() -> None:
    ontology_path = Path(sys.argv[1])
    spines_json = sys.argv[2]  # JSON list
    out_tsv = Path(sys.argv[3])
    out_meta = Path(sys.argv[4])

    match_spines = set(json.loads(spines_json))
    raw = load_ontology(ontology_path)
    idx, meta = concept_index(raw, match_spines)

    rows = []
    for norm, cands in sorted(idx.items()):
        for c in cands:
            rows.append(
                {
                    "term_norm": norm,
                    "xrm_id": c["xrm_id"],
                    "preferred_label": c["preferred_label"],
                    "spine": c["spine"],
                    "matched_label": c["matched_label"],
                    "label_kind": c["label_kind"],
                }
            )
    write_tsv(
        out_tsv,
        rows,
        ["term_norm", "xrm_id", "preferred_label", "spine", "matched_label", "label_kind"],
    )
    out_meta.parent.mkdir(parents=True, exist_ok=True)
    out_meta.write_text(
        json.dumps(
            {
                "n_labels": len(rows),
                "n_concepts": len(meta),
                "match_spines": sorted(match_spines),
                "concepts": meta,
            },
            indent=2,
        )
        + "\n"
    )
    print(f"[ontology_index] labels={len(rows)} concepts={len(meta)} → {out_tsv}")


if __name__ == "__main__":
    main()
