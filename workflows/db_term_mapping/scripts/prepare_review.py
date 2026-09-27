#!/usr/bin/env python3
"""Emit uncertain matches for adjudication."""
from __future__ import annotations

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib_match import write_tsv  # noqa: E402

REVIEW_BINS = {"fuzzy_mid", "fuzzy_high", "compositional", "alias"}


def main() -> None:
    matches_path = Path(sys.argv[1])
    out_path = Path(sys.argv[2])

    rows = []
    with matches_path.open() as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            if row["confidence"] in REVIEW_BINS or (
                row["confidence"] == "unmatched" and int(row["count"]) >= 5
            ):
                # Always queue fuzzy_mid + compositional; fuzzy_high/alias for spot-check;
                # unmatched with count>=5 for gap triage
                if row["confidence"] in {"fuzzy_mid", "compositional"}:
                    priority = "required"
                elif row["confidence"] == "unmatched":
                    priority = "gap_candidate"
                else:
                    priority = "spot_check"
                rows.append(
                    {
                        **row,
                        "review_priority": priority,
                        "decision": "",
                        "adj_xrm_id": "",
                        "adj_preferred_label": "",
                        "adj_note": "",
                    }
                )

    # Sort: required first, then by count desc
    pri = {"required": 0, "spot_check": 1, "gap_candidate": 2}
    rows.sort(key=lambda r: (pri.get(r["review_priority"], 9), -int(r["count"]), r["term"]))

    cols = [
        "review_priority",
        "source",
        "term",
        "count",
        "confidence",
        "match_method",
        "score",
        "xrm_id",
        "preferred_label",
        "spine",
        "matched_label",
        "compositional_head",
        "candidates",
        "notes",
        "decision",
        "adj_xrm_id",
        "adj_preferred_label",
        "adj_note",
    ]
    write_tsv(out_path, rows, cols)
    print(f"[review_queue] {len(rows)} rows → {out_path}")


if __name__ == "__main__":
    main()
