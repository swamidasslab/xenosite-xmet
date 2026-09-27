#!/usr/bin/env python3
"""First-pass confidence-binned matching of source terms → XRM."""
from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

from rapidfuzz import fuzz, process

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib_antonym import antonym_relation, negation_variants  # noqa: E402
from lib_match import (  # noqa: E402
    compositional_head,
    load_aliases,
    normalize_label,
    write_tsv,
)


def load_index(path: Path) -> dict[str, list[dict[str, str]]]:
    idx: dict[str, list[dict[str, str]]] = defaultdict(list)
    with path.open() as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            idx[row["term_norm"]].append(row)
    return idx


def pick_best(cands: list[dict[str, str]]) -> dict[str, str]:
    """Prefer prefLabel hits, then chemical transformation / phase spines."""
    spine_rank = {
        "chemical transformation": 0,
        "phase I reaction family": 1,
        "phase II conjugation family": 1,
        "metabolism phase": 2,
        "reactive metabolite family": 3,
        "structural delta": 4,
        "site type": 5,
        "leaving group": 6,
        "medchem liability": 7,
        "pharmacological role": 8,
    }

    def key(c: dict[str, str]):
        return (
            0 if c.get("label_kind") == "pref" else 1,
            spine_rank.get(c.get("spine", ""), 9),
            c.get("xrm_id", ""),
        )

    return sorted(cands, key=key)[0]


def main() -> None:
    terms_path = Path(sys.argv[1])
    index_path = Path(sys.argv[2])
    aliases_path = Path(sys.argv[3])
    out_path = Path(sys.argv[4])
    summary_path = Path(sys.argv[5])
    fuzzy_high_min = float(sys.argv[6])
    fuzzy_mid_min = float(sys.argv[7])
    fuzzy_margin = float(sys.argv[8])

    idx = load_index(index_path)
    aliases = load_aliases(aliases_path)
    choices = list(idx.keys())

    rows_in = []
    with terms_path.open() as fh:
        rows_in = list(csv.DictReader(fh, delimiter="\t"))

    out_rows = []
    bin_counts: dict[str, int] = defaultdict(int)

    for row in rows_in:
        term = row["term"]
        source = row["source"]
        term_norm = row.get("term_norm") or normalize_label(term)
        count = int(row["count"])

        confidence = "unmatched"
        match_method = ""
        xrm_id = ""
        preferred_label = ""
        spine = ""
        matched_label = ""
        score = ""
        candidates = ""
        notes = ""
        head = compositional_head(term)

        # 1) curated alias
        if term_norm in aliases:
            a = aliases[term_norm]
            confidence = "alias"
            match_method = "alias_table"
            xrm_id = a["xrm_id"]
            preferred_label = a["preferred_label"]
            matched_label = term
            notes = a.get("note", "")
            # fill spine from index if present
            for cands in idx.values():
                for c in cands:
                    if c["xrm_id"] == xrm_id:
                        spine = c["spine"]
                        if not preferred_label:
                            preferred_label = c["preferred_label"]
                        break
                if spine:
                    break

        # 2) exact
        elif term_norm in idx:
            best = pick_best(idx[term_norm])
            confidence = (
                "exact_pref" if best["label_kind"] == "pref" else "exact_synonym"
            )
            match_method = "exact"
            xrm_id = best["xrm_id"]
            preferred_label = best["preferred_label"]
            spine = best["spine"]
            matched_label = best["matched_label"]
            score = "100"

        # 3) compositional with exact/synonym head
        elif head and head in idx:
            best = pick_best(idx[head])
            confidence = "compositional"
            match_method = "compositional_head"
            xrm_id = best["xrm_id"]
            preferred_label = best["preferred_label"]
            spine = best["spine"]
            matched_label = best["matched_label"]
            notes = f"head={head}"
            score = "100"

        # 3b) antonym via negation prefix against ontology labels
        elif any(normalize_label(v) in idx for v in negation_variants(term)):
            for v in negation_variants(term):
                vn = normalize_label(v)
                if vn not in idx:
                    continue
                best = pick_best(idx[vn])
                rel = antonym_relation(term, best["matched_label"]) or antonym_relation(
                    term, best["preferred_label"]
                )
                if not rel:
                    # still treat as antonym if negation variant hit
                    rel = {"stem": vn, "source_is_negative": True}
                confidence = "antonym_of"
                match_method = "negation_prefix"
                xrm_id = best["xrm_id"]
                preferred_label = best["preferred_label"]
                spine = best["spine"]
                matched_label = best["matched_label"]
                score = "100"
                notes = (
                    f"antonym_of={preferred_label}; "
                    f"source_is_negative={rel.get('source_is_negative')}; "
                    f"mint_or_link_inverse"
                )
                break

        # 4) fuzzy
        else:
            if choices:
                hits = process.extract(
                    term_norm,
                    choices,
                    scorer=fuzz.token_sort_ratio,
                    limit=5,
                )
            else:
                hits = []
            if hits:
                top_score, top_label = hits[0][1], hits[0][0]
                second = hits[1][1] if len(hits) > 1 else 0.0
                margin = top_score - second
                cand_strs = [
                    f"{lab}:{sc:.0f}:{pick_best(idx[lab])['xrm_id']}"
                    for lab, sc, _ in hits
                ]
                candidates = " || ".join(cand_strs)
                best = pick_best(idx[top_label])
                rel = antonym_relation(term, best["matched_label"]) or antonym_relation(
                    term, best["preferred_label"]
                )
                if rel and top_score >= fuzzy_mid_min:
                    confidence = "antonym_of"
                    match_method = "fuzzy_antonym_negation"
                    xrm_id = best["xrm_id"]
                    preferred_label = best["preferred_label"]
                    spine = best["spine"]
                    matched_label = best["matched_label"]
                    score = f"{top_score:.1f}"
                    notes = (
                        f"antonym_of={preferred_label}; stem={rel['stem']}; "
                        f"source_is_negative={rel['source_is_negative']}; "
                        f"margin={margin:.1f}; mint_or_link_inverse"
                    )
                elif top_score >= fuzzy_high_min and margin >= fuzzy_margin:
                    confidence = "fuzzy_high"
                    match_method = "fuzzy_token_sort"
                    xrm_id = best["xrm_id"]
                    preferred_label = best["preferred_label"]
                    spine = best["spine"]
                    matched_label = best["matched_label"]
                    score = f"{top_score:.1f}"
                    notes = f"margin={margin:.1f}"
                elif top_score >= fuzzy_mid_min:
                    confidence = "fuzzy_mid"
                    match_method = "fuzzy_token_sort"
                    xrm_id = best["xrm_id"]
                    preferred_label = best["preferred_label"]
                    spine = best["spine"]
                    matched_label = best["matched_label"]
                    score = f"{top_score:.1f}"
                    notes = f"margin={margin:.1f}; needs review"
                elif head:
                    # compositional head not in index — still flag
                    confidence = "compositional"
                    match_method = "compositional_head_unmatched"
                    notes = f"head={head} (head not in ontology index)"
                else:
                    confidence = "unmatched"
                    match_method = "none"
                    score = f"{top_score:.1f}"
                    notes = "best below mid threshold"
            elif head:
                confidence = "compositional"
                match_method = "compositional_head_unmatched"
                notes = f"head={head} (head not in ontology index)"
            else:
                confidence = "unmatched"
                match_method = "none"

        bin_counts[confidence] += 1
        out_rows.append(
            {
                "source": source,
                "term": term,
                "term_norm": term_norm,
                "count": count,
                "confidence": confidence,
                "match_method": match_method,
                "score": score,
                "xrm_id": xrm_id,
                "preferred_label": preferred_label,
                "spine": spine,
                "matched_label": matched_label,
                "compositional_head": head or "",
                "candidates": candidates,
                "notes": notes,
            }
        )

    cols = [
        "source",
        "term",
        "term_norm",
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
    ]
    write_tsv(out_path, out_rows, cols)

    # occurrence-weighted tallies
    by_conf_occ: dict[str, int] = defaultdict(int)
    for r in out_rows:
        by_conf_occ[r["confidence"]] += int(r["count"])

    summary = {
        "n_terms": len(out_rows),
        "by_confidence_terms": dict(bin_counts),
        "by_confidence_occurrences": dict(by_conf_occ),
        "fuzzy_high_min": fuzzy_high_min,
        "fuzzy_mid_min": fuzzy_mid_min,
        "fuzzy_margin": fuzzy_margin,
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2) + "\n")
    print(f"[match] {dict(bin_counts)} → {out_path}")


if __name__ == "__main__":
    main()
