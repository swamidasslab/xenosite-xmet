#!/usr/bin/env python3
"""Forest rule/pattern coverage via SPARQL over SKOS + SSSOM.

Loads:
  - ``data/ontology/xmet.ttl`` (hierarchy: ``skos:broader``)
  - ``data/mappings/xmet-forest.sssom.tsv`` (asserted as ``skos:*Match`` triples)

Infers (exactMatch only — closeMatch does not join):

    forestEntity xmet:covers ?child
      ← forestEntity skos:exactMatch ?parent
         ∧ ?child skos:broader+ ?parent
      (also covers the exactMatch home itself)

Writes ``data/candidates/forest-inferred-covers.ttl`` and prints overlap stats.

Usage:
  make forest-pattern-coverage
  uv run python tools/forest_pattern_coverage.py
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, RDFS, SKOS

ROOT = Path(__file__).resolve().parents[1]
SKOS_TTL = ROOT / "data/ontology/xmet.ttl"
SSSOM = ROOT / "data/mappings/xmet-forest.sssom.tsv"
HARVEST = ROOT / "data/candidates/forest-smarts.jsonl"
OUT_TTL = ROOT / "data/candidates/forest-inferred-covers.ttl"
OUT_JSON = ROOT / "data/candidates/forest-pattern-coverage.json"

XMET = Namespace("https://xenosite.org/ontology/xmet#")
FOREST = Namespace("https://xenosite.org/ns/forest/")
# Custom cover predicate (materialized inference)
COVERS = XMET.covers  # xmet:covers


def curie_to_iri(curie: str) -> URIRef:
    if curie.startswith("xmet:"):
        return XMET[curie[5:]]
    if curie.startswith("forest.rule:"):
        return FOREST[f"rule/{curie.split(':', 1)[1]}"]
    if curie.startswith("forest.pattern:"):
        return FOREST[f"pattern/{curie.split(':', 1)[1]}"]
    if curie.startswith("forest.ruleset:"):
        return FOREST[f"ruleset/{curie.split(':', 1)[1]}"]
    raise ValueError(f"unknown CURIE: {curie}")


def iri_to_curie(term) -> str:
    s = str(term)
    if s.startswith(str(XMET)):
        return "xmet:" + s[len(str(XMET)) :]
    if s.startswith(str(FOREST) + "rule/"):
        return "forest.rule:" + s[len(str(FOREST) + "rule/") :]
    if s.startswith(str(FOREST) + "pattern/"):
        return "forest.pattern:" + s[len(str(FOREST) + "pattern/") :]
    if s.startswith(str(FOREST) + "ruleset/"):
        return "forest.ruleset:" + s[len(str(FOREST) + "ruleset/") :]
    return s


PRED = {
    "skos:exactMatch": SKOS.exactMatch,
    "skos:closeMatch": SKOS.closeMatch,
    "skos:relatedMatch": SKOS.relatedMatch,
    "exactMatch": SKOS.exactMatch,
    "closeMatch": SKOS.closeMatch,
    "relatedMatch": SKOS.relatedMatch,
}


def load_graph(skos_ttl: Path, sssom: Path) -> Graph:
    g = Graph()
    g.bind("skos", SKOS)
    g.bind("xmet", XMET)
    g.bind("forest", FOREST)
    g.parse(skos_ttl, format="turtle")

    raw = sssom.read_text().splitlines()
    hdr = next(i for i, line in enumerate(raw) if line.startswith("subject_id"))
    for row in csv.DictReader(
        (line for line in raw[hdr:] if line.strip()), delimiter="\t"
    ):
        pred = PRED.get(row["predicate_id"]) or PRED.get(
            row["predicate_id"].split(":")[-1]
        )
        if pred is None:
            continue
        subj = curie_to_iri(row["subject_id"])
        obj = curie_to_iri(row["object_id"])
        # Assert Forest → XMET (and reverse skos from subject side as authored)
        g.add((subj, pred, obj))
        if row.get("subject_label"):
            g.add((subj, SKOS.prefLabel, Literal(row["subject_label"])))
        if row.get("object_label"):
            g.add((obj, RDFS.label, Literal(row["object_label"])))
    return g


# exactMatch home covers itself and all SKOS descendants (broader+ toward root:
# child skos:broader+ parent means child is under parent).
INFER_COVERS = """
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX xmet: <https://xenosite.org/ontology/xmet#>

CONSTRUCT {
    ?forest xmet:covers ?home .
    ?forest xmet:covers ?child .
}
WHERE {
    ?home skos:exactMatch ?forest .
    FILTER( STRSTARTS(STR(?forest), "https://xenosite.org/ns/forest/") )
    {
        BIND(?home AS ?child)
    }
    UNION
    {
        ?child skos:broader+ ?home .
    }
}
"""

STATS_ASSERTED = """
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

SELECT ?kind (COUNT(DISTINCT ?forest) AS ?n)
WHERE {
  ?home skos:exactMatch ?forest .
  FILTER( STRSTARTS(STR(?forest), "https://xenosite.org/ns/forest/") )
  BIND(
    IF( CONTAINS(STR(?forest), "/rule/"), "rule",
    IF( CONTAINS(STR(?forest), "/pattern/"), "pattern",
    IF( CONTAINS(STR(?forest), "/ruleset/"), "ruleset", "other" ) ) )
    AS ?kind
  )
}
GROUP BY ?kind
ORDER BY ?kind
"""

STATS_PRED = """
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

SELECT ?pred (COUNT(*) AS ?n)
WHERE {
  VALUES ?pred { skos:exactMatch skos:closeMatch skos:relatedMatch }
  ?s ?pred ?forest .
  FILTER( STRSTARTS(STR(?forest), "https://xenosite.org/ns/forest/") )
}
GROUP BY ?pred
ORDER BY ?pred
"""

# Per forest entity: exact home + inferred cover count
PER_FOREST = """
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX xmet: <https://xenosite.org/ontology/xmet#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?forest ?home ?homeLabel (COUNT(DISTINCT ?covered) AS ?nCovered)
WHERE {
  ?home skos:exactMatch ?forest .
  FILTER( STRSTARTS(STR(?forest), "https://xenosite.org/ns/forest/") )
  OPTIONAL { ?home skos:prefLabel ?homeLabel }
  ?forest xmet:covers ?covered .
}
GROUP BY ?forest ?home ?homeLabel
ORDER BY ?forest
"""

# Rule vs pattern XMET home overlap (exactMatch subjects)
HOME_SETS = """
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

SELECT ?home ?asRule ?asPattern
WHERE {
  {
    SELECT DISTINCT ?home WHERE {
      ?home skos:exactMatch ?f .
      FILTER( STRSTARTS(STR(?f), "https://xenosite.org/ns/forest/") )
    }
  }
  BIND( EXISTS {
    ?home skos:exactMatch ?r .
    FILTER( CONTAINS(STR(?r), "/rule/") )
  } AS ?asRule )
  BIND( EXISTS {
    ?home skos:exactMatch ?p .
    FILTER( CONTAINS(STR(?p), "/pattern/") )
  } AS ?asPattern )
}
ORDER BY ?home
"""

# Pattern home under its sibling rule class home?
PATTERN_VS_RULE = """
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

SELECT ?pattern ?patternHome ?rule ?ruleHome ?rel
WHERE {
  ?patternHome skos:exactMatch ?pattern .
  FILTER( CONTAINS(STR(?pattern), "/pattern/") )
  # forest.pattern:Class/name → forest.rule:Class
  BIND( IRI(
    CONCAT(
      "https://xenosite.org/ns/forest/rule/",
      STRBEFORE( STRAFTER(STR(?pattern), "/pattern/"), "/" )
    )
  ) AS ?rule )
  OPTIONAL { ?ruleHome skos:exactMatch ?rule }
  BIND(
    IF( !BOUND(?ruleHome), "no_rule_home",
    IF( ?patternHome = ?ruleHome, "same_home",
    IF( EXISTS { ?patternHome skos:broader+ ?ruleHome }, "under_rule",
    IF( EXISTS { ?ruleHome skos:broader+ ?patternHome }, "above_rule",
        "disjoint" ) ) ) )
    AS ?rel
  )
}
ORDER BY ?pattern
"""


def load_harvest_patterns(path: Path) -> set[str]:
    if not path.exists():
        return set()
    out: set[str] = set()
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        tag = json.loads(line).get("forest_tag") or ""
        if tag.startswith("forest.pattern:"):
            out.add(tag)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--skos", type=Path, default=SKOS_TTL)
    ap.add_argument("--sssom", type=Path, default=SSSOM)
    ap.add_argument("--harvest", type=Path, default=HARVEST)
    ap.add_argument(
        "--json",
        action="store_true",
        help=f"Also write summary JSON to {OUT_JSON.name}",
    )
    ap.add_argument(
        "--verbose",
        action="store_true",
        help="Print per-class / per-pattern detail",
    )
    args = ap.parse_args()

    if not args.skos.exists():
        print(f"missing {args.skos}; run: make ontology-export", file=sys.stderr)
        return 1

    g = load_graph(args.skos, args.sssom)
    inferred = g.query(INFER_COVERS).graph
    # Merge covers into working graph for follow-up queries
    for triple in inferred:
        g.add(triple)

    OUT_TTL.parent.mkdir(parents=True, exist_ok=True)
    out_g = Graph()
    out_g.bind("skos", SKOS)
    out_g.bind("xmet", XMET)
    out_g.bind("forest", FOREST)
    for triple in inferred:
        out_g.add(triple)
    # Also keep asserted exactMatch for readability
    for s, p, o in g.triples((None, SKOS.exactMatch, None)):
        if str(o).startswith(str(FOREST)) or str(s).startswith(str(FOREST)):
            out_g.add((s, p, o))
    out_g.serialize(OUT_TTL, format="turtle")

    print("Forest ↔ pattern coverage")
    print(f"  sources: {args.skos.name} + {args.sssom.name}")
    print(f"  wrote:   {OUT_TTL.relative_to(ROOT)}")

    kind_n = {str(r.kind): int(r.n) for r in g.query(STATS_ASSERTED)}
    pred_n = {
        str(r.pred).rsplit("#", 1)[-1]: int(r.n) for r in g.query(STATS_PRED)
    }
    print(
        f"  SSSOM exactMatch: {kind_n.get('rule', 0)} rules, "
        f"{kind_n.get('pattern', 0)} patterns"
        + (f", {kind_n['ruleset']} rulesets" if kind_n.get("ruleset") else "")
        + f"  (close={pred_n.get('closeMatch', 0)}, "
        f"related={pred_n.get('relatedMatch', 0)})"
    )

    both = rule_only = pat_only = 0
    both_ids: list[str] = []
    rule_only_ids: list[str] = []
    for r in g.query(HOME_SETS):
        home = iri_to_curie(r.home)
        ar, ap = bool(r.asRule), bool(r.asPattern)
        if ar and ap:
            both += 1
            both_ids.append(home)
        elif ar:
            rule_only += 1
            rule_only_ids.append(home)
        elif ap:
            pat_only += 1
    print(
        f"  XMET homes: {both} shared, {rule_only} rule-only, "
        f"{pat_only} pattern-only"
    )

    rel_c: Counter[str] = Counter()
    by_class: dict[str, list] = defaultdict(list)
    for r in g.query(PATTERN_VS_RULE):
        rel = str(r.rel)
        rel_c[rel] += 1
        pat = iri_to_curie(r.pattern)
        cls = pat.split(":", 1)[1].split("/", 1)[0]
        by_class[cls].append(
            {
                "pattern": pat,
                "pattern_home": iri_to_curie(r.patternHome),
                "rule": iri_to_curie(r.rule) if r.rule else None,
                "rule_home": iri_to_curie(r.ruleHome) if r.ruleHome else None,
                "rel": rel,
            }
        )
    rel_bits = ", ".join(f"{k}={v}" for k, v in sorted(rel_c.items()))
    print(f"  pattern↔rule home: {rel_bits}")

    cover_n = {
        iri_to_curie(r.forest): int(r.nCovered) for r in g.query(PER_FOREST)
    }
    n_covers = sum(1 for _ in inferred)
    print(
        f"  inferred xmet:covers: {n_covers} triples "
        f"across {len(cover_n)} forest entities"
    )

    harvest = load_harvest_patterns(args.harvest)
    sssom_pats = {
        iri_to_curie(o)
        for _s, _p, o in g.triples((None, SKOS.exactMatch, None))
        if str(o).startswith(str(FOREST) + "pattern/")
    }
    if args.harvest.exists():
        print(
            f"  harvest↔SSSOM patterns: ∩={len(harvest & sssom_pats)}  "
            f"harvest-only={len(harvest - sssom_pats)}  "
            f"sssom-only={len(sssom_pats - harvest)}"
        )

    # Gaps only (not full per-class dump)
    rules_no_pat = sorted(
        cls
        for cls in (
            iri_to_curie(r.forest).split(":", 1)[1]
            for r in g.query(PER_FOREST)
            if iri_to_curie(r.forest).startswith("forest.rule:")
        )
        if cls not in by_class
    )
    pats_no_rule = sorted(cls for cls, rows in by_class.items() if all(
        e["rel"] == "no_rule_home" for e in rows
    ))
    disjoint = sum(1 for rows in by_class.values() for e in rows if e["rel"] == "disjoint")
    if rules_no_pat:
        print(f"  gap: rules with no patterns: {', '.join(rules_no_pat)}")
    if pats_no_rule:
        print(f"  gap: pattern classes with no rule home: {', '.join(pats_no_rule)}")
    if disjoint:
        print(f"  gap: {disjoint} patterns disjoint from rule home")
    harvest_only = sorted(harvest - sssom_pats)
    if harvest_only:
        print(f"  gap: harvest-only patterns: {', '.join(harvest_only)}")

    if args.verbose:
        print()
        print("Per class (--verbose)")
        rule_homes = {}
        for r in g.query(PER_FOREST):
            fc = iri_to_curie(r.forest)
            if not fc.startswith("forest.rule:"):
                continue
            rule_homes[fc.split(":", 1)[1]] = (
                iri_to_curie(r.home),
                str(r.homeLabel or ""),
                int(r.nCovered),
            )
        for cls in sorted(set(rule_homes) | set(by_class)):
            rh = rule_homes.get(cls)
            hdr = (
                f"{cls}: rule→{rh[0]} ({rh[1]}) covers={rh[2]}"
                if rh
                else f"{cls}: (no rule exactMatch)"
            )
            print(f"  {hdr}  patterns={len(by_class.get(cls, []))}")
            for e in by_class.get(cls, []):
                print(
                    f"    {e['pattern'].split(':', 1)[1]:40s}  "
                    f"{e['pattern_home']}  {e['rel']:12s}  "
                    f"covers={cover_n.get(e['pattern'], 0)}"
                )

    summary = {
        "skos": str(args.skos.relative_to(ROOT)),
        "sssom": str(args.sssom.relative_to(ROOT)),
        "inferred_ttl": str(OUT_TTL.relative_to(ROOT)),
        "exactMatch_kinds": kind_n,
        "predicates": pred_n,
        "pattern_vs_rule": dict(rel_c),
        "homes": {
            "both": both_ids,
            "rule_only": rule_only_ids,
            "pattern_only_count": pat_only,
        },
        "n_cover_triples": n_covers,
        "gaps": {
            "rules_no_patterns": rules_no_pat,
            "pattern_classes_no_rule": pats_no_rule,
            "disjoint_patterns": disjoint,
            "harvest_only": harvest_only,
        },
        "harvest": {
            "n": len(harvest),
            "sssom_patterns": len(sssom_pats),
            "intersection": len(harvest & sssom_pats),
            "harvest_only": harvest_only,
        },
    }
    if args.json:
        OUT_JSON.write_text(json.dumps(summary, indent=2) + "\n")
        print(f"  json:    {OUT_JSON.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
