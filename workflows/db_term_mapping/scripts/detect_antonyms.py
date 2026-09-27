#!/usr/bin/env python3
"""Enumerate negation-prefix antonym pairs between source terms and XMET labels."""
from __future__ import annotations

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib_antonym import antonym_relation, negation_variants  # noqa: E402
from lib_match import normalize_label, write_tsv  # noqa: E402


def main() -> None:
    terms_path = Path(sys.argv[1])
    index_path = Path(sys.argv[2])
    out_path = Path(sys.argv[3])

    labels = []
    with index_path.open() as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            labels.append(row)

    by_norm = {}
    for row in labels:
        by_norm.setdefault(row["term_norm"], row)

    pairs = []
    with terms_path.open() as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            term = row["term"]
            # Against each ontology label via antonym_relation (expensive but OK ~300×900)
            # Faster: only check negation variants then exact index
            found = False
            for v in negation_variants(term):
                vn = normalize_label(v)
                hit = by_norm.get(vn)
                if not hit:
                    continue
                rel = antonym_relation(term, hit["matched_label"]) or antonym_relation(
                    term, hit["preferred_label"]
                )
                pairs.append(
                    {
                        "source": row["source"],
                        "term": term,
                        "count": row["count"],
                        "antonym_xrm_id": hit["xrm_id"],
                        "antonym_preferred_label": hit["preferred_label"],
                        "antonym_matched_label": hit["matched_label"],
                        "stem": (rel or {}).get("stem", ""),
                        "source_is_negative": (rel or {}).get("source_is_negative", ""),
                        "method": "negation_variant_index",
                    }
                )
                found = True
                break
            if found:
                continue
            # fuzzy-style: compare to preferred labels sharing stem after strip
            for hit in labels:
                if hit["label_kind"] != "pref":
                    continue
                rel = antonym_relation(term, hit["preferred_label"])
                if not rel:
                    continue
                pairs.append(
                    {
                        "source": row["source"],
                        "term": term,
                        "count": row["count"],
                        "antonym_xrm_id": hit["xrm_id"],
                        "antonym_preferred_label": hit["preferred_label"],
                        "antonym_matched_label": hit["matched_label"],
                        "stem": rel.get("stem", ""),
                        "source_is_negative": rel.get("source_is_negative", ""),
                        "method": "stem_antonym",
                    }
                )
                break

    write_tsv(
        out_path,
        pairs,
        [
            "source",
            "term",
            "count",
            "antonym_xrm_id",
            "antonym_preferred_label",
            "antonym_matched_label",
            "stem",
            "source_is_negative",
            "method",
        ],
    )
    print(f"[antonyms] {len(pairs)} pairs → {out_path}")


if __name__ == "__main__":
    main()
