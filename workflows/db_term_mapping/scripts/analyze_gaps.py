#!/usr/bin/env python3
"""Classify residual terms into gap buckets for one dataset."""
from __future__ import annotations

import csv
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib_match import normalize_label, write_tsv  # noqa: E402

OUT_OF_SCOPE = re.compile(
    r"\b(optical resolution|photolysis|radiolysis|plasma protein|"
    r"inversion|condensation|unknown reaction)\b",
    re.I,
)
BROAD = re.compile(
    r"^(c-?oxidation|oxidation|reduction|hydrolysis|conjugation|o-conjugation|"
    r"n-conjugation|phase\s*[i12]+|biotransformation|metabolism)$",
    re.I,
)
PRODUCT_OR_LIABILITY = re.compile(
    r"\b(dna|protein|covalent)\s*bind|\badduct\b|\breactive\b",
    re.I,
)

BUCKET_HELP = {
    "site_compositional": "Qualified phrases; head already in XRM — use bundles/templates",
    "existing_facet_gap": "Likely missing leaf/synonym under an existing reaction facet",
    "broad_class": "Coarse umbrella needing systematic child mapping",
    "coverage_decision_exclude": "Propose exclude from reaction-type spine",
    "coverage_decision_other_spine": "May belong on another XRM spine",
    "coverage_decision_unknown": "Needs a human cover/exclude decision",
    "needs_adjudication": "Algorithm match present; decision still open",
    "antonym_link": "Negation antonym of existing leaf — mint inverse + related_match",
}


def classify(row: dict[str, str]) -> tuple[str, str]:
    term = row["term"]
    n = normalize_label(term)
    status = row.get("final_status", "")
    head = (row.get("compositional_head") or "").strip()
    conf = row.get("confidence", "")
    final_conf = (row.get("final_confidence") or conf or "").lower()
    adj_note = row.get("adjudication_note") or ""

    if status == "antonym_pending":
        return (
            "antonym_link",
            adj_note
            or "Negation-prefix antonym of an existing XRM leaf; mint inverse + related_match.",
        )

    if status == "compositional_held" or (conf == "compositional" and row.get("xrm_id")):
        return (
            "site_compositional",
            "Site-/substrate-qualified phrase whose reaction head already maps; "
            "prefer site_type + transformation bundle, not a new leaf concept.",
        )

    if status == "rejected":
        if "out_of_scope" in final_conf:
            return ("coverage_decision_exclude", adj_note or "adjudicated out of scope")
        if "compositional_only" in final_conf:
            return (
                "site_compositional",
                adj_note or "adjudicated as process/compositional only",
            )
        # no_match / reject after review
        if BROAD.match(n) or "umbrella" in adj_note.lower() or "broad" in adj_note.lower():
            return ("broad_class", adj_note or "rejected umbrella / coarse label")
        if OUT_OF_SCOPE.search(n) or OUT_OF_SCOPE.search(term):
            return ("coverage_decision_exclude", adj_note or "out of reaction-type scope")
        if "antonym" in adj_note.lower() or "inverse" in adj_note.lower():
            return (
                "existing_facet_gap",
                adj_note or "inverse/antonym of an existing leaf — decide whether to mint",
            )
        if re.search(
            r"(dealkyl|demethyl|hydroxyl|glucuron|sulfat|oxid|reduct|hydrolys|"
            r"acetyl|methylat|glutath|epoxid|deacyl|acylat|decarbox|ester|"
            r"glycos|lactam|lacton|formyl|nitros|chain|cycliz)",
            n,
        ):
            return (
                "existing_facet_gap",
                adj_note or "rejected auto-match; likely real reaction-type gap",
            )
        return (
            "coverage_decision_unknown",
            adj_note or "rejected; cover/exclude still open",
        )

    if OUT_OF_SCOPE.search(n) or OUT_OF_SCOPE.search(term):
        return (
            "coverage_decision_exclude",
            "Likely out of XRM reaction-type scope (binding / optical / non-metabolic).",
        )

    if PRODUCT_OR_LIABILITY.search(n) and "conjugat" not in n:
        return (
            "coverage_decision_other_spine",
            "May belong on reactive metabolite / liability / evidence spines, not reaction type.",
        )

    if BROAD.match(n) or n in {
        "c-oxidation",
        "o-conjugation",
        "n-conjugation",
        "s-conjugation",
        "oxidation",
        "reduction",
        "hydrolysis",
        "conjugation",
    }:
        return (
            "broad_class",
            "Umbrella / coarse label that needs systematic child inventory or explicit maps to existing parents.",
        )

    if status == "uncertain" and row.get("xrm_id"):
        return (
            "needs_adjudication",
            "Algorithm proposed a match but confidence below auto-accept.",
        )

    if head and not row.get("xrm_id"):
        return (
            "existing_facet_gap",
            f"Compositional head {head!r} missing from ontology index — likely a leaf gap under an existing spine.",
        )

    if re.match(r"^[ons]-", n) or re.search(
        r"(dealkyl|demethyl|hydroxyl|glucuron|sulfat|sulfon|oxid|reduct|"
        r"hydrolys|acetyl|methylat|glutath|epoxid|deacyl|acylat|dehalogen|"
        r"decarbox|aromatiz|hydrogenat|dehydrogen)",
        n,
    ):
        return (
            "existing_facet_gap",
            "Looks like a xenobiotic reaction-type leaf that should sit under an existing transformation/conjugation facet.",
        )

    return (
        "coverage_decision_unknown",
        "No clear reaction-type reading; decide whether to cover, map elsewhere, or exclude.",
    )


def main() -> None:
    residual_path = Path(sys.argv[1])
    strong_path = Path(sys.argv[2])
    match_summary_path = Path(sys.argv[3])
    condense_summary_path = Path(sys.argv[4])
    dataset = sys.argv[5]
    out_tsv = Path(sys.argv[6])
    out_md = Path(sys.argv[7])
    examples_per = int(sys.argv[8])

    residual = list(csv.DictReader(residual_path.open(), delimiter="\t"))
    strong = list(csv.DictReader(strong_path.open(), delimiter="\t"))
    match_summary = json.loads(match_summary_path.read_text())
    condense_summary = json.loads(condense_summary_path.read_text())

    classified = []
    bucket_terms: Counter[str] = Counter()
    bucket_occ: Counter[str] = Counter()
    examples: dict[str, list[dict[str, str]]] = defaultdict(list)

    for row in residual:
        bucket, rationale = classify(row)
        bucket_terms[bucket] += 1
        bucket_occ[bucket] += int(row["count"])
        rec = {**row, "gap_bucket": bucket, "gap_rationale": rationale}
        classified.append(rec)
        if len(examples[bucket]) < examples_per:
            examples[bucket].append(rec)

    classified.sort(
        key=lambda r: (r["gap_bucket"], -int(r["count"]), r["term"])
    )
    write_tsv(
        out_tsv,
        classified,
        [
            "gap_bucket",
            "gap_rationale",
            "source",
            "term",
            "count",
            "final_status",
            "final_confidence",
            "confidence",
            "xrm_id",
            "preferred_label",
            "compositional_head",
            "candidates",
            "notes",
            "adjudication_note",
        ],
    )

    strong_occ = sum(int(r["count"]) for r in strong)
    all_occ = strong_occ + sum(int(r["count"]) for r in residual)
    n_terms = len(strong) + len(residual)

    lines = [
        f"# {dataset} reaction terms → XRM mapping analysis",
        "",
        "**Ontology fills applied for approved categories** (reactive-metabolite binding,",
        "cyanide, antonym inverses, high-count facet gaps). Further mid-fuzzy adjudication still open.",
        "",
        "This report covers **one dataset only** (not merged with the other).",
        "",
        "## Summary",
        "",
        f"- Dataset: **`{dataset}`**",
        f"- Source terms scored: **{match_summary['n_terms']}**",
        f"- Strong-confidence matches: **{condense_summary['n_strong_terms']}** terms "
        f"({condense_summary['strong_occurrences']} occurrences; "
        f"{100 * condense_summary['strong_occurrence_fraction']:.1f}% of labeled occurrences).",
        f"- Residual (not strong): **{condense_summary['n_nonstrong_terms']}** terms "
        f"({all_occ - strong_occ} occurrences).",
        f"- Term coverage (strong/all): **{100 * len(strong) / n_terms:.1f}%**"
        if n_terms
        else "- Term coverage: n/a",
        "",
        "### First-pass confidence bins (pre-adjudication)",
        "",
        "| Confidence | Terms | Occurrences |",
        "| --- | ---: | ---: |",
    ]
    for k in sorted(match_summary["by_confidence_terms"]):
        lines.append(
            f"| `{k}` | {match_summary['by_confidence_terms'][k]} | "
            f"{match_summary['by_confidence_occurrences'].get(k, 0)} |"
        )

    lines += [
        "",
        "## Residual gap buckets",
        "",
        "Terms that did **not** land in the high-quality strong-match list.",
        "",
        "| Bucket | Terms | Occurrences | Meaning |",
        "| --- | ---: | ---: | --- |",
    ]
    for b, n in bucket_terms.most_common():
        lines.append(
            f"| `{b}` | {n} | {bucket_occ[b]} | {BUCKET_HELP.get(b, '')} |"
        )

    for b, _ in bucket_terms.most_common():
        lines += [
            "",
            f"### `{b}`",
            "",
            BUCKET_HELP.get(b, ""),
            "",
            "| Term | Count | Notes |",
            "| --- | ---: | --- |",
        ]
        for ex in examples[b]:
            note = (
                ex.get("compositional_head")
                or ex.get("preferred_label")
                or ex.get("notes")
                or ""
            ).replace("|", "/")
            lines.append(f"| {ex['term']} | {ex['count']} | {note} |")

    lines += [
        "",
        "## Recommended next actions (not yet executed)",
        "",
        f"1. **Accept** `data/derived/db_term_mapping/{dataset}/strong_matches.tsv` as the crosswalk seed for this dataset.",
        "2. **Site compositional**: do not mint combinatorial concepts; use site_type + templates.",
        "3. **Existing facet gaps**: review high-count leaves for synonym adds vs new concepts.",
        "4. **Broad classes**: map umbrellas as `broadMatch` to parents; child inventory separately.",
        "5. **Coverage excludes**: confirm binding / optical / non-metabolic stay off reaction-type spine.",
        "",
        "Artifacts (this dataset):",
        "",
        f"- `data/derived/db_term_mapping/{dataset}/matches_scored.tsv`",
        f"- `data/derived/db_term_mapping/{dataset}/strong_matches.tsv`",
        f"- `data/derived/db_term_mapping/{dataset}/residual_terms.tsv`",
        f"- `data/derived/db_term_mapping/{dataset}/gap_analysis.tsv`",
        f"- `workflows/db_term_mapping/resources/adjudications_{dataset}.tsv`",
        "",
    ]
    out_md.write_text("\n".join(lines) + "\n")
    print(f"[gaps] {dataset} buckets={dict(bucket_terms)} → {out_md}")


if __name__ == "__main__":
    main()
