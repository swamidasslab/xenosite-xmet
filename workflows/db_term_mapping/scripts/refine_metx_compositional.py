#!/usr/bin/env python3
"""Decompose MetXBioDB compositional reaction phrases into XRM facets.

For each compositional residual/match, decide:
  composite_covered  — head + site/attachment facets already in XRM
  partial_composite  — head covered; some qualifier facets missing
  novel_facet        — introduces a concept beyond identity+site composition

Writes:
  data/derived/db_term_mapping/metxbiodb/compositional_refinement.tsv
  data/derived/db_term_mapping/metxbiodb/compositional_refinement.md
"""
from __future__ import annotations

import csv
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib_match import compositional_head, normalize_label, write_tsv  # noqa: E402

REPO = Path(__file__).resolve().parents[3]


def load_site_and_transform_labels(ontology_path: Path) -> tuple[list[str], list[str]]:
    raw = yaml.safe_load(ontology_path.read_text())
    spines = {s["id"]: s["preferred_label"] for s in raw["spines"]}
    by_id = {c["id"]: c for c in raw["concepts"]}
    for s in raw["spines"]:
        by_id[s["id"]] = {**s, "parents": []}

    def nearest(cid, seen=None):
        seen = seen or set()
        if cid in spines:
            return cid
        if cid in seen or cid not in by_id:
            return None
        seen.add(cid)
        for p in by_id[cid].get("parents") or []:
            r = nearest(p, seen)
            if r:
                return r
        return None

    sites, transforms = [], []
    for c in raw["concepts"]:
        sname = spines.get(nearest(c["id"]) or "", "")
        labs = [c["preferred_label"], *(c.get("synonyms") or [])]
        if sname == "site type":
            sites.extend(labs)
        if sname in {
            "chemical transformation",
            "phase I reaction family",
            "phase II conjugation family",
            "leaving group",
        }:
            transforms.extend(labs)
    return [normalize_label(x) for x in sites], [normalize_label(x) for x in transforms]


# Qualifier cues → preferred site concepts (normalized labels in site spine)
QUALIFIER_MAP = [
    (re.compile(r"phenol|\bphenolic|-oh\b|aromatic -oh", re.I), ["phenol", "phenolic site"]),
    (re.compile(r"\baromatic\b|\baryl\b|\bbenzene\b", re.I), ["aromatic site"]),
    (re.compile(r"\baliphatic\b|\balkyl\b", re.I), ["terminal alkyl"]),
    (re.compile(r"\balicyclic\b|\bcyclo", re.I), ["alicyclic site"]),
    (re.compile(r"\btertiary amine\b", re.I), ["tertiary amine", "tertiary amine site"]),
    (re.compile(r"\bsecondary amine\b", re.I), ["secondary amine"]),
    (re.compile(r"\bprimary amine\b|\barylamine\b", re.I), ["primary amine", "aniline"]),
    (re.compile(r"\bbenzylic\b|adjacent to aromatic|methyl carbon adjacent to aromatic", re.I), ["benzylic site", "benzylic carbon"]),
    (re.compile(r"\bfused benzene\b|\bfused\b", re.I), ["fused benzene site", "aromatic site"]),
    (re.compile(r"\bpara\b|para-hydrox", re.I), []),  # regio handled by head
    (re.compile(r"\bortho\b|ortho-hydrox", re.I), []),
    (re.compile(r"\bmeta\b|meta-hydrox", re.I), []),
    (re.compile(r"\bterminal methyl\b|\bomega\b|ω", re.I), ["terminal alkyl"]),
    (re.compile(r"\ballylic\b", re.I), ["allylic site"]),
    (re.compile(r"\bcarboxylic acid\b|\baliphatic acid\b", re.I), ["carboxylic acid"]),
    (re.compile(r"\bether\b|\baryl ether\b", re.I), ["aryl ether", "alkyl ether"]),
    (re.compile(r"\borganohalide\b|\bhalide\b", re.I), ["alkyl halide"]),
    (re.compile(r"\bcarbonyl\b|\bketo\b", re.I), ["alpha to heteroatom"]),
]


NOVEL_CUES = [
    (re.compile(r"\bnot adjacent\b|\badjacent to substituted\b", re.I), "adjacency/regiochemistry rule beyond site type"),
    (re.compile(r"\bmonosubstituted benzene\b|\bdisubstituted benzene\b", re.I), "substitution pattern class (optional site facet)"),
    (re.compile(r"\borganphosph|\bphosphorothio|\bthioate\b|\bdithioate\b", re.I), "organophosphorus chemotype (coverage decision)"),
    (re.compile(r"\bbenzodiazepine\b|\bcoumarin\b|\boxoazaphosphorine\b|\bsterol\b", re.I), "scaffold-specific label (prefer out-of-scope or example-only)"),
    (re.compile(r"\bcholine\b|\btrimethylamine\b", re.I), "named biochemical pathway label"),
    (re.compile(r"\bdemethoxymethylation\b|\bdechloroethylation\b|\bdehydroxyethylation\b", re.I), "specific leaving-group leaf under dealkylation"),
    (re.compile(r"\bring (opening|fission|cleavage)\b|\bmethylenedioxy\b", re.I), "ring-opening / methylenedioxy process facet"),
]


def analyze_term(term: str, head: str, site_norms: set[str], xrm_id: str) -> dict:
    n = normalize_label(term)
    matched_facets = []
    missing_facets = []
    novel = []

    if head:
        matched_facets.append(f"head:{head}")
    if xrm_id:
        matched_facets.append(f"xrm:{xrm_id}")

    for pat, labels in QUALIFIER_MAP:
        if pat.search(term) or pat.search(n):
            for lab in labels:
                ln = normalize_label(lab)
                if ln in site_norms or ln.replace(" ", "-") in site_norms:
                    matched_facets.append(f"site:{lab}")
                else:
                    # still count as intended facet even if not in site spine (may be transform)
                    if any(ln == normalize_label(h) or ln in normalize_label(h) for h in [head or ""]):
                        matched_facets.append(f"via_head:{lab}")
                    elif ln in site_norms:
                        matched_facets.append(f"site:{lab}")
                    else:
                        # check loose containment in site set
                        hit = next((s for s in site_norms if ln in s or s in ln), None)
                        if hit:
                            matched_facets.append(f"site:{lab}")
                        else:
                            missing_facets.append(lab)

    for pat, why in NOVEL_CUES:
        if pat.search(term) or pat.search(n):
            novel.append(why)

    # Dedup
    matched_facets = list(dict.fromkeys(matched_facets))
    missing_facets = list(dict.fromkeys(missing_facets))
    novel = list(dict.fromkeys(novel))

    if novel and not matched_facets:
        bucket = "novel_facet"
    elif novel:
        bucket = "novel_facet"
    elif missing_facets and head:
        bucket = "partial_composite"
    elif head and matched_facets:
        bucket = "composite_covered"
    elif head:
        bucket = "partial_composite"
    else:
        bucket = "novel_facet"

    # If only scaffold-specific novel cue and head+site ok → still novel_facet for the scaffold part
    return {
        "compositional_bucket": bucket,
        "head": head or "",
        "matched_facets": " | ".join(matched_facets),
        "missing_facets": " | ".join(missing_facets),
        "novel_concepts": " | ".join(novel),
    }


def main() -> None:
    matches_path = Path(sys.argv[1])
    ontology_path = Path(sys.argv[2])
    out_tsv = Path(sys.argv[3])
    out_md = Path(sys.argv[4])

    site_labs, _ = load_site_and_transform_labels(ontology_path)
    site_norms = set(site_labs)

    rows_in = list(csv.DictReader(matches_path.open(), delimiter="\t"))
    # Prefer compositional confidence rows; also residual compositional_held later via same file
    comp = [
        r
        for r in rows_in
        if r.get("confidence") == "compositional"
        or r.get("compositional_head")
        or " of " in r["term"].lower()
        or " -oh " in f" {r['term'].lower()} "
    ]
    # unique by term
    seen = set()
    uniq = []
    for r in sorted(comp, key=lambda x: -int(x["count"])):
        if r["term"] in seen:
            continue
        seen.add(r["term"])
        uniq.append(r)

    out_rows = []
    buckets = Counter()
    examples = defaultdict(list)
    for r in uniq:
        head = r.get("compositional_head") or compositional_head(r["term"]) or ""
        analysis = analyze_term(r["term"], head, site_norms, r.get("xrm_id") or "")
        buckets[analysis["compositional_bucket"]] += 1
        row = {
            "term": r["term"],
            "count": r["count"],
            "confidence": r.get("confidence", ""),
            "xrm_id": r.get("xrm_id", ""),
            "preferred_label": r.get("preferred_label", ""),
            **analysis,
        }
        out_rows.append(row)
        if len(examples[analysis["compositional_bucket"]]) < 15:
            examples[analysis["compositional_bucket"]].append(row)

    write_tsv(
        out_tsv,
        out_rows,
        [
            "compositional_bucket",
            "term",
            "count",
            "head",
            "matched_facets",
            "missing_facets",
            "novel_concepts",
            "confidence",
            "xrm_id",
            "preferred_label",
        ],
    )

    lines = [
        "# MetXBioDB compositional refinement",
        "",
        "Decomposes site-/substrate-qualified Reaction Type phrases into existing XRM",
        "facets vs concepts that still need coverage.",
        "",
        f"- Phrases analyzed: **{len(out_rows)}**",
        "",
        "| Bucket | Terms | Meaning |",
        "| --- | ---: | --- |",
        f"| `composite_covered` | {buckets['composite_covered']} | Head + site/attachment already expressible as XRM composites |",
        f"| `partial_composite` | {buckets['partial_composite']} | Head known; some qualifier facets missing |",
        f"| `novel_facet` | {buckets['novel_facet']} | Extra concept beyond chemical identity + standard site |",
        "",
    ]
    for b in ["composite_covered", "partial_composite", "novel_facet"]:
        lines += [f"### `{b}`", "", "| Term | Count | Head | Matched | Missing / novel |", "| --- | ---: | --- | --- | --- |"]
        for ex in examples[b]:
            extra = ex["missing_facets"] or ex["novel_concepts"] or ""
            lines.append(
                f"| {ex['term']} | {ex['count']} | {ex['head']} | {ex['matched_facets'][:60]} | {extra[:80]} |"
            )
        lines.append("")

    lines += [
        "## Recommendation",
        "",
        "- **composite_covered**: do not mint; rely on annotation bundles (transformation + site_type).",
        "- **partial_composite**: mint only the missing site/process leaves listed in `missing_facets`.",
        "- **novel_facet**: decide cover (new leaf) vs exclude (scaffold-specific / pathway names).",
        "",
    ]
    out_md.write_text("\n".join(lines) + "\n")
    print(f"[metx_compositional] {dict(buckets)} → {out_md}")


if __name__ == "__main__":
    main()
