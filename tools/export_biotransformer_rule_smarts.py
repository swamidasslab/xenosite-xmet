#!/usr/bin/env python3
"""Export BioTransformer per-pattern reactant/exclusion SMARTS + SMIRKS.

Writes ``data/mappings/biotransformer-rule-smarts.tsv`` for curation reference.
Multiple SMARTS of the same role are joined with `` | `` (ordinal order).
"""

from __future__ import annotations

import csv
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BT_DIR = ROOT.parent / "xenosite-data" / "data" / "Biotransformer"
OUT = ROOT / "data/mappings/biotransformer-rule-smarts.tsv"
STEM_RE = re.compile(r"_PATTERN\d+[A-Z]?$")


def main() -> None:
    if not BT_DIR.is_dir():
        raise SystemExit(f"BioTransformer data not found: {BT_DIR}")

    rxn = list(csv.DictReader((BT_DIR / "reactions.csv").open()))
    smarts = list(csv.DictReader((BT_DIR / "reaction_smarts.csv").open()))

    by: dict[tuple[str, str], dict[str, list[tuple[int, str]]]] = defaultdict(
        lambda: {"reactant": [], "excluded": []}
    )
    for s in smarts:
        role = (s.get("role") or "").strip()
        if role not in ("reactant", "excluded"):
            continue
        key = (s["source"], s["reaction_id"])
        by[key][role].append((int(s.get("ordinal") or 0), s.get("smarts") or ""))
    for key in by:
        for role in ("reactant", "excluded"):
            by[key][role].sort()

    fields = [
        "source",
        "reaction_id",
        "btmr_id",
        "common_name",
        "bt_object_id",
        "n_reactant_smarts",
        "reactant_smarts",
        "n_excluded_smarts",
        "excluded_smarts",
        "smirks",
    ]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, delimiter="\t", lineterminator="\n")
        w.writeheader()
        for r in sorted(rxn, key=lambda x: (x["source"], x["reaction_id"])):
            key = (r["source"], r["reaction_id"])
            react = [s for _, s in by[key]["reactant"]]
            excl = [s for _, s in by[key]["excluded"]]
            stem = STEM_RE.sub("", r["reaction_id"])
            w.writerow(
                {
                    "source": r["source"],
                    "reaction_id": r["reaction_id"],
                    "btmr_id": r.get("btmr_id") or "",
                    "common_name": r.get("common_name") or "",
                    "bt_object_id": f"bt:{stem}",
                    "n_reactant_smarts": len(react),
                    "reactant_smarts": " | ".join(react),
                    "n_excluded_smarts": len(excl),
                    "excluded_smarts": " | ".join(excl),
                    "smirks": r.get("smirks") or "",
                }
            )

    n_excl = sum(1 for r in rxn if by[(r["source"], r["reaction_id"])]["excluded"])
    print(f"wrote {len(rxn)} rules → {OUT.relative_to(ROOT)}")
    print(f"  with exclusion SMARTS: {n_excl}")


if __name__ == "__main__":
    main()
