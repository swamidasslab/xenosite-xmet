#!/usr/bin/env python3
"""Apply adjudications and emit strong-confidence matches + residual unmatched."""
from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib_match import load_adjudications, normalize_label, write_tsv  # noqa: E402

# Auto-accepted without adjudication
AUTO_STRONG = {"exact_pref", "exact_synonym", "alias", "fuzzy_high"}

# Decisions in adjudications.tsv
ACCEPT = {"accept", "accept_as", "synonym_of"}
REJECT = {"reject", "no_match", "out_of_scope", "compositional_only"}
ANTONYM_ACCEPT = {"accept_antonym", "antonym_of"}


def main() -> None:
    matches_path = Path(sys.argv[1])
    adj_path = Path(sys.argv[2])
    strong_path = Path(sys.argv[3])
    unmatched_path = Path(sys.argv[4])
    summary_path = Path(sys.argv[5])

    adjs = load_adjudications(adj_path)

    strong = []
    unmatched = []
    stats = defaultdict(int)

    with matches_path.open() as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            key = (row["source"], normalize_label(row["term"]))
            adj = adjs.get(key)

            status = "pending"
            xrm_id = row["xrm_id"]
            preferred_label = row["preferred_label"]
            spine = row["spine"]
            confidence = row["confidence"]
            decision_note = ""

            if adj:
                decision = (adj.get("decision") or "").strip().lower()
                decision_note = adj.get("adj_note") or adj.get("note") or ""
                if decision in ACCEPT or decision in ANTONYM_ACCEPT:
                    status = "strong"
                    confidence = f"adjudicated:{decision}"
                    if (adj.get("adj_xrm_id") or "").strip():
                        xrm_id = adj["adj_xrm_id"].strip()
                    if (adj.get("adj_preferred_label") or "").strip():
                        preferred_label = adj["adj_preferred_label"].strip()
                    if (adj.get("spine") or "").strip():
                        spine = adj["spine"].strip()
                elif decision in REJECT:
                    status = "rejected"
                    confidence = f"adjudicated:{decision}"
                    xrm_id = ""
                    preferred_label = ""
                    spine = ""
                else:
                    status = "pending"
                    decision_note = f"unknown decision={decision!r}; {decision_note}"
            elif row["confidence"] in AUTO_STRONG and row["xrm_id"]:
                status = "strong"
            elif row["confidence"] == "antonym_of" and row["xrm_id"]:
                # Linked to the opposite concept until inverse leaf is minted / rematched
                status = "antonym_pending"
                decision_note = row.get("notes", "")
            elif row["confidence"] == "compositional" and row["xrm_id"]:
                status = "compositional_held"
            else:
                status = "unmatched" if not row["xrm_id"] else "uncertain"

            stats[status] += 1
            out = {
                **row,
                "final_status": status,
                "final_confidence": confidence,
                "final_xrm_id": xrm_id,
                "final_preferred_label": preferred_label,
                "final_spine": spine,
                "adjudication_note": decision_note,
            }
            if status == "strong":
                strong.append(out)
            else:
                unmatched.append(out)

    strong_cols = [
        "source",
        "term",
        "term_norm",
        "count",
        "final_status",
        "final_confidence",
        "final_xrm_id",
        "final_preferred_label",
        "final_spine",
        "matched_label",
        "match_method",
        "score",
        "adjudication_note",
    ]
    write_tsv(strong_path, strong, strong_cols)

    um_cols = [
        "source",
        "term",
        "term_norm",
        "count",
        "final_status",
        "final_confidence",
        "confidence",
        "xrm_id",
        "preferred_label",
        "spine",
        "compositional_head",
        "candidates",
        "notes",
        "adjudication_note",
    ]
    write_tsv(unmatched_path, unmatched, um_cols)

    strong_occ = sum(int(r["count"]) for r in strong)
    total_occ = sum(int(r["count"]) for r in strong) + sum(int(r["count"]) for r in unmatched)
    summary = {
        "n_strong_terms": len(strong),
        "n_nonstrong_terms": len(unmatched),
        "strong_occurrences": strong_occ,
        "total_occurrences": total_occ,
        "strong_occurrence_fraction": round(strong_occ / total_occ, 4) if total_occ else 0,
        "by_final_status": dict(stats),
        "auto_strong_bins": sorted(AUTO_STRONG),
    }
    summary_path.write_text(json.dumps(summary, indent=2) + "\n")
    print(f"[condense] strong={len(strong)} residual={len(unmatched)} → {strong_path}")


if __name__ == "__main__":
    main()
