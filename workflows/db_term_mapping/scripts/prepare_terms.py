#!/usr/bin/env python3
"""Prepare a single dataset's reaction-type term inventory (no cross-source union)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib_match import normalize_label, read_term_counts, write_tsv  # noqa: E402


def main() -> None:
    counts_path = Path(sys.argv[1])
    source = sys.argv[2]
    out_path = Path(sys.argv[3])

    rows = read_term_counts(counts_path, source)
    for r in rows:
        r["term_norm"] = normalize_label(r["term"])

    write_tsv(out_path, rows, ["source", "term", "term_norm", "count", "field"])
    print(f"[prepare_terms] {source}: {len(rows)} terms → {out_path}")


if __name__ == "__main__":
    main()
