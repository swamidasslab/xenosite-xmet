#!/usr/bin/env python3
"""Expand competency questions ~10× across all categories.

Reads ontology + assignments + SSSOM, writes:
  data/competency/cq.yml
  data/competency/gold/curated_reactions.tsv

Hand-curated SPARQL / SHACL seeds are preserved and padded with generated
ontology_broader, ontology_labels, mapping_exists, and tagging CQs.
"""
from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
YAML_PATH = ROOT / "data/ontology/xmet.yaml"
ASSIGN = ROOT / "data/assignments/xenobiotic.jsonl"
MAP_DIR = ROOT / "data/mappings"
CQ_OUT = ROOT / "data/competency/cq.yml"
GOLD_OUT = ROOT / "data/competency/gold/curated_reactions.tsv"

# Approximate 10× of the original ~55-CQ budget.
TARGETS = {
    "P1": 100,
    "P2": 100,
    "RM": 80,
    "SITE": 80,
    "DELTA": 50,
    "MAP": 50,
    "EV": 20,
    "PROV": 20,
    "LG": 25,
    "PHARM": 15,
    "ABOUT": 10,
    "MED": 40,
}

SPINES = {
    "P1": ("xmet:4000213", "chemical transformation"),
    "P2": ("xmet:1300000", "phase II conjugation family"),
    "RM": ("xmet:1500000", "reactive metabolite family"),
    "SITE": ("xmet:1600000", "site type"),
    "DELTA": ("xmet:4000220", "structural delta"),
    "EV": ("xmet:2000000", "evidence"),
    "PROV": ("xmet:1900000", "rule provenance"),
    "LG": ("xmet:4000229", "leaving group"),
    "PHARM": ("xmet:2300000", "pharmacological role"),
    "ABOUT": ("xmet:2400000", "annotation about"),
    "MED": ("xmet:1400000", "medchem liability"),
}

# Secondary P1 spine for family-class broader checks.
P1_FAMILY = "xmet:1200000"


def load():
    doc = yaml.safe_load(YAML_PATH.read_text())
    by_id = {c["id"]: c for c in doc["concepts"]}
    by_label = {c["preferred_label"]: c for c in doc["concepts"]}
    children = defaultdict(list)
    for c in doc["concepts"]:
        for p in c.get("parents") or []:
            children[p].append(c["id"])
    return doc, by_id, by_label, children


def descendants(children, root):
    out = set()
    stack = list(children.get(root, []))
    while stack:
        x = stack.pop()
        if x in out:
            continue
        out.add(x)
        stack.extend(children.get(x, []))
    return out


def ancestors(by_id, cid):
    out = set()
    stack = list(by_id.get(cid, {}).get("parents") or [])
    while stack:
        p = stack.pop()
        if not p or p in out:
            continue
        out.add(p)
        stack.extend(by_id.get(p, {}).get("parents") or [])
    return out


def load_sssom():
    rows = []
    for path in sorted(MAP_DIR.glob("*.sssom.tsv")):
        for line in path.read_text().splitlines():
            if not line or line.startswith("#") or line.startswith("subject"):
                continue
            parts = line.split("\t")
            if len(parts) >= 3:
                rows.append(
                    {
                        "subject": parts[0],
                        "predicate": parts[1],
                        "object": parts[2],
                        "subject_label": parts[4] if len(parts) > 4 else "",
                    }
                )
    return rows


def load_tag_rules(by_id):
    rules = []
    for line in ASSIGN.read_text().splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        o = json.loads(line)
        tags = o.get("tags_any") or []
        if not tags:
            continue
        emit_labels = []
        for eid in o.get("emit") or []:
            c = by_id.get(eid)
            if c:
                emit_labels.append(c["preferred_label"])
        rules.append(
            {
                "id": o["id"],
                "tags": tags,
                "emit": o.get("emit") or [],
                "emit_labels": emit_labels,
            }
        )
    return rules


def chunk(xs, n):
    for i in range(0, len(xs), n):
        yield xs[i : i + n]


def seed_questions():
    """Hand-curated high-value CQs (SPARQL/SHACL/tagging demos)."""
    return [
        # --- Phase I seeds ---
        {
            "id": "CQ-P1-001",
            "layer": "ontology",
            "question": "Hydroxylation family labels under chemical transformation.",
            "type": "ontology_labels",
            "under": "xmet:4000213",
            "expected_contains_labels": [
                "hydroxylation",
                "aromatic hydroxylation",
                "aliphatic hydroxylation",
            ],
        },
        {
            "id": "CQ-P1-002",
            "layer": "ontology",
            "question": "Rainbow unstable oxygenation under phase I reaction family.",
            "type": "ontology_broader",
            "concept": "xmet:4000005",
            "expected_ancestors": ["xmet:1200000"],
        },
        {
            "id": "CQ-P1-003",
            "layer": "tagging",
            "question": "Ethane→ethanol tags aliphatic hydroxylation + phase I.",
            "type": "tagging",
            "reactant": "CC",
            "product": "CCO",
            "tags": [],
            "expected_labels": [
                "hydroxylation",
                "aliphatic hydroxylation",
                "phase I",
                "stable oxygenation",
            ],
            "expected_excludes_labels": ["aromatic hydroxylation"],
        },
        {
            "id": "CQ-P1-004",
            "layer": "tagging",
            "question": "Ethene→epoxide tags epoxidation without hydroxylation.",
            "type": "tagging",
            "reactant": "C=C",
            "product": "C1CO1",
            "tags": [],
            "expected_labels": ["epoxidation", "phase I"],
            "expected_excludes_labels": ["hydroxylation"],
        },
        {
            "id": "CQ-P1-005",
            "layer": "ontology",
            "question": "Find transformations that can produce aldehydes.",
            "type": "sparql",
            "query": "sparql/cq_aldehyde_producers.rq",
            "expected_contains": ["xmet:4000043", "xmet:4000349"],
            "expected_excludes": ["xmet:4000148"],
        },
        # --- Phase II seeds ---
        {
            "id": "CQ-P2-001",
            "layer": "ontology",
            "question": "Phase II includes glucuronidation, sulfation, glutathionation.",
            "type": "ontology_labels",
            "under": "xmet:1300000",
            "expected_contains_labels": [
                "glucuronidation",
                "sulfation",
                "glutathionation",
            ],
        },
        {
            "id": "CQ-P2-002",
            "layer": "ontology",
            "question": "Which Phase II reactions attach through oxygen?",
            "type": "sparql",
            "query": "sparql/cq_phase2_oxygen_attachment.rq",
            "expected_contains": [
                "xmet:4000149",
                "xmet:4000159",
                "xmet:4000176",
                "xmet:4000149",
                "xmet:4000159",
                "xmet:4000176",
            ],
            "expected_excludes": [
                "xmet:4000153",
                "xmet:4000153",
                "xmet:4000152",
                "xmet:4000152",
            ],
        },
        {
            "id": "CQ-P2-003",
            "layer": "ontology",
            "question": "Glucuronidation classes distinguish O/N/S/C/acyl attachment.",
            "type": "sparql",
            "query": "sparql/cq_glucuronidation_attachment_atoms.rq",
            "expected_contains": [
                "xmet:4000149",
                "xmet:4000153",
                "xmet:4000152",
                "xmet:4000155",
                "xmet:4000156",
            ],
            "min_results": 5,
        },
        {
            "id": "CQ-P2-004",
            "layer": "tagging",
            "question": "Forest Glucuronidation emits glucuronidation + phase II.",
            "type": "tagging",
            "reactant": "CCO",
            "product": "CCO",
            "tags": ["forest.rule:Glucuronidation"],
            "expected_labels": ["glucuronidation", "phase II", "glucuronide conjugate"],
        },
        {
            "id": "CQ-P2-005",
            "layer": "ontology",
            "question": "Phase II nitrogen attachment SPARQL.",
            "type": "sparql",
            "query": "sparql/cq_phase2_nitrogen_attachment.rq",
            "expected_contains": ["xmet:4000153", "xmet:4000153"],
            "expected_excludes": ["xmet:4000149", "xmet:4000149"],
        },
        {
            "id": "CQ-P2-006",
            "layer": "ontology",
            "question": "Phase II not enzyme-specific.",
            "type": "sparql",
            "query": "sparql/cq_phase2_not_enzyme.rq",
            "expected_contains": ["xmet:4000148", "xmet:4000158", "xmet:4000167"],
        },
        # --- RM seeds ---
        {
            "id": "CQ-RM-001",
            "layer": "ontology",
            "question": "Reactive metabolite family core classes.",
            "type": "ontology_labels",
            "under": "xmet:1500000",
            "expected_contains_labels": [
                "quinone",
                "epoxide",
                "aldehyde",
                "GSH-trappable metabolite",
            ],
        },
        {
            "id": "CQ-RM-002",
            "layer": "ontology",
            "question": "Quinone-like but not strict quinone.",
            "type": "sparql",
            "query": "sparql/cq_quinone_like_not_strict.rq",
            "expected_contains": ["xmet:1500011", "xmet:1500100", "xmet:1500103"],
            "expected_excludes": ["xmet:1500010"],
        },
        {
            "id": "CQ-RM-003",
            "layer": "ontology",
            "question": "GSH-trappable producers.",
            "type": "sparql",
            "query": "sparql/cq_gsh_trappable_producers.rq",
            "expected_contains": [
                "xmet:4000022",
                "xmet:4000059",
                "xmet:4000152",
                "xmet:4000167",
            ],
        },
        {
            "id": "CQ-RM-004",
            "layer": "ontology",
            "question": "Reactive aromatic metabolites SPARQL.",
            "type": "sparql",
            "query": "sparql/cq_reactive_aromatic_metabolites.rq",
            "expected_contains": [
                "xmet:1500010",
                "xmet:1500012",
                "xmet:1500104",
                "xmet:1500017",
            ],
        },
        {
            "id": "CQ-RM-005",
            "layer": "tagging",
            "question": "forms reactive conjugate tag emits.",
            "type": "tagging",
            "reactant": "C",
            "product": "C",
            "tags": ["chem:forms-reactive-conjugate"],
            "expected_labels": ["forms reactive conjugate", "reactive conjugate"],
        },
        # --- SITE seeds ---
        {
            "id": "CQ-SITE-001",
            "layer": "ontology",
            "question": "Core site environments.",
            "type": "ontology_labels",
            "under": "xmet:1600000",
            "expected_contains_labels": [
                "benzylic site",
                "tertiary amine site",
                "phenolic site",
            ],
        },
        {
            "id": "CQ-SITE-002",
            "layer": "ontology",
            "question": "Site environments SPARQL.",
            "type": "sparql",
            "query": "sparql/cq_site_environments.rq",
            "expected_contains": [
                "xmet:1600014",
                "xmet:1600015",
                "xmet:1600021",
                "xmet:1600022",
                "xmet:1600103",
                "xmet:1600130",
            ],
            "min_results": 5,
        },
        {
            "id": "CQ-SITE-003",
            "layer": "tagging",
            "question": "Localized benzylic hydroxylation @1.",
            "type": "tagging",
            "reactant": "[CH3:1]c1ccc([CH3:2])cc1",
            "product": "O[CH2:1]c1ccc([CH3:2])cc1",
            "tags": ["chem:benzylic-hydroxylation@1"],
            "expected_labels": ["benzylic hydroxylation"],
            "expect_site_map": [1],
        },
        {
            "id": "CQ-SITE-004",
            "layer": "tagging",
            "question": "Bond-centered epoxidation site localization.",
            "type": "tagging",
            "reactant": "[CH2:1]=[CH2:2]",
            "product": "C1OC1",
            "tags": ["chem:epoxidation@1,2"],
            "expected_labels": ["epoxidation"],
            "expect_site_map": [1, 2],
            "expect_site_label_substring": "@",
        },
        # --- DELTA seeds ---
        {
            "id": "CQ-DELTA-001",
            "layer": "ontology",
            "question": "Structural delta core labels.",
            "type": "ontology_labels",
            "under": "xmet:4000220",
            "expected_contains_labels": [
                "monooxygenation",
                "formula delta",
                "oxygen gain",
            ],
        },
        {
            "id": "CQ-DELTA-002",
            "layer": "ontology",
            "question": "Structural delta SPARQL.",
            "type": "sparql",
            "query": "sparql/cq_structural_deltas.rq",
            "expected_contains": ["xmet:4000223", "xmet:7700001", "xmet:1700010"],
            "min_results": 3,
        },
        {
            "id": "CQ-DELTA-003",
            "layer": "tagging",
            "question": "Ethane→ethanol emits oxygen gain.",
            "type": "tagging",
            "reactant": "CC",
            "product": "CCO",
            "tags": [],
            "expected_labels": ["oxygen gain"],
        },
        # --- MAP / EV / PROV seeds ---
        {
            "id": "CQ-MAP-001",
            "layer": "mapping",
            "question": "Hydroxylation maps to MOP.",
            "type": "mapping_exists",
            "subject": "xmet:4000012",
            "object_prefix": "mop:",
        },
        {
            "id": "CQ-MAP-002",
            "layer": "mapping",
            "question": "Xenobiotic biotransformation → GO:0006805.",
            "type": "mapping_exists",
            "subject": "xmet:4000000",
            "object": "GO:0006805",
        },
        {
            "id": "CQ-EV-001",
            "layer": "ontology",
            "question": "Definition coverage complete.",
            "type": "definition_coverage",
            "min_fraction": 1.0,
        },
        {
            "id": "CQ-PROV-001",
            "layer": "ontology",
            "question": "SHACL core shape for all concepts.",
            "type": "shacl",
            "shapes": "../ontology/xmet.shacl.ttl",
            "data": "../ontology/xmet.ttl",
            "allow_warnings": False,
        },
        {
            "id": "CQ-LG-001",
            "layer": "ontology",
            "question": "Leaving group spine core.",
            "type": "ontology_labels",
            "under": "xmet:4000229",
            "expected_contains_labels": [
                "methyl leaving group",
                "halide leaving group",
                "carboxylate leaving group",
            ],
        },
        {
            "id": "CQ-PHARM-001",
            "layer": "ontology",
            "question": "Pharmacological role distinctions.",
            "type": "ontology_labels",
            "under": "xmet:2300000",
            "expected_contains_labels": [
                "pharmacologically active metabolite",
                "pharmacologically inactive metabolite",
                "prodrug",
            ],
        },
        {
            "id": "CQ-ABOUT-001",
            "layer": "ontology",
            "question": "Annotation-about parent/product/reaction.",
            "type": "ontology_labels",
            "under": "xmet:2400000",
            "expected_contains_labels": [
                "about parent",
                "about product",
                "about reaction",
            ],
        },
        {
            "id": "CQ-ABOUT-002",
            "layer": "tagging",
            "question": "Prodrug + active metabolite about roles.",
            "type": "tagging",
            "reactant": "C",
            "product": "C",
            "tags": [
                "chem:prodrug",
                "chem:active-metabolite",
                "chem:about-parent",
                "chem:about-product",
            ],
            "expected_labels": [
                "prodrug",
                "pharmacologically active metabolite",
                "about parent",
                "about product",
            ],
        },
        {
            "id": "CQ-MED-001",
            "layer": "ontology",
            "question": "Medchem liability includes soft spot and bioactivation.",
            "type": "ontology_labels",
            "under": "xmet:1400000",
            "expected_contains_labels": [
                "metabolic soft spot",
                "bioactivation",
                "aldehyde forming",
            ],
        },
    ]


def pick_primary_labels(emit_labels, limit=3):
    """Prefer short, non-ruleset chemist labels for tagging expectations."""
    skip = re.compile(
        r"(ruleset|rule$|/|Forest-map|SMARTS|underspec|unspecified|family$)",
        re.I,
    )
    out = []
    for lab in emit_labels:
        if skip.search(lab):
            continue
        if lab not in out:
            out.append(lab)
        if len(out) >= limit:
            break
    if not out and emit_labels:
        out = emit_labels[:1]
    return out


def sparql_under_spine(spine_id: str, concept_id: str) -> str:
    local_spine = spine_id.split(":", 1)[1]
    local_c = concept_id.split(":", 1)[1]
    return f"""PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX xmet: <https://xenosite.org/ontology/xmet#>
SELECT DISTINCT ?term WHERE {{
  BIND(xmet:{local_c} AS ?term)
  ?term skos:broader+ xmet:{local_spine} .
}}
"""


def expand_category(
    cat,
    target,
    by_id,
    children,
    tag_rules,
    sssom,
    used_ids,
):
    """Fill category with a balanced mix (~25% each major type)."""
    spine = SPINES.get(cat)
    desc = descendants(children, spine[0]) if spine else set()
    leaves = sorted(
        [cid for cid in desc if cid in by_id],
        key=lambda c: by_id[c]["preferred_label"],
    )
    labels = [by_id[c]["preferred_label"] for c in leaves]

    # Budgets (sum ≈ target). Tagging/mapping capped by available rules.
    n_sparql = max(4, target // 4)
    n_tag = max(4, target // 4)
    n_labels = max(4, target // 5)
    n_map = max(2, target // 10)
    n_broader = max(4, target - (n_sparql + n_tag + n_labels + n_map))

    buckets = {
        "sparql": [],
        "tagging": [],
        "ontology_labels": [],
        "mapping_exists": [],
        "ontology_broader": [],
    }

    for cid in leaves:
        if len(buckets["sparql"]) >= n_sparql:
            break
        buckets["sparql"].append(
            {
                "id": "TMP",
                "layer": "ontology",
                "question": f"SPARQL: {by_id[cid]['preferred_label']} under {spine[1]}.",
                "type": "sparql",
                "query_text": sparql_under_spine(spine[0], cid),
                "expected_contains": [cid],
                "min_results": 1,
            }
        )

    # Prefer expecting transformation / phase-family labels from emit lists.
    # Product-class companions are covered by relatedMatch expansion + gold gaps,
    # not by asserting every former ad-hoc emit id.
    chem_desc = set()
    for root in ("xmet:4000213", "xmet:1200000", "xmet:1300000"):
        chem_desc |= descendants(children, root)

    seen_tags = set()
    for rule in tag_rules:
        if len(buckets["tagging"]) >= n_tag:
            break
        # Primary expects: emits in this category spine that are also chem transforms,
        # else any emit in this spine (for RM/SITE/MED-native tags).
        primary_ids = [e for e in rule["emit"] if e in desc and e in chem_desc]
        if not primary_ids:
            primary_ids = [e for e in rule["emit"] if e in desc]
        if not primary_ids:
            continue
        tag = next((t for t in rule["tags"] if t.startswith("chem:")), None)
        if not tag:
            tag = rule["tags"][0]
        base_tag = tag.split("@", 1)[0]
        if base_tag in seen_tags:
            continue
        seen_tags.add(base_tag)
        expect = pick_primary_labels(
            [by_id[e]["preferred_label"] for e in primary_ids if e in by_id],
            limit=2,
        )
        if not expect:
            continue
        buckets["tagging"].append(
            {
                "id": "TMP",
                "layer": "tagging",
                "question": f"Tag {base_tag} emits {expect[0]} ({cat}).",
                "type": "tagging",
                "reactant": "C",
                "product": "C",
                "tags": [base_tag],
                "expected_labels": expect,
            }
        )

    for batch in chunk(labels, 3):
        if len(buckets["ontology_labels"]) >= n_labels:
            break
        buckets["ontology_labels"].append(
            {
                "id": "TMP",
                "layer": "ontology",
                "question": f"Labels present under {spine[1]}: {', '.join(batch)}.",
                "type": "ontology_labels",
                "under": spine[0],
                "expected_contains_labels": list(batch),
            }
        )

    for row in sssom:
        if len(buckets["mapping_exists"]) >= n_map:
            break
        if row["subject"] not in desc:
            continue
        buckets["mapping_exists"].append(
            {
                "id": "TMP",
                "layer": "mapping",
                "question": f"{row['subject_label'] or row['subject']} maps to {row['object']}.",
                "type": "mapping_exists",
                "subject": row["subject"],
                "object": row["object"],
            }
        )

    for cid in leaves:
        if len(buckets["ontology_broader"]) >= n_broader:
            break
        buckets["ontology_broader"].append(
            {
                "id": "TMP",
                "layer": "ontology",
                "question": f"{by_id[cid]['preferred_label']} hangs under {spine[1]}.",
                "type": "ontology_broader",
                "concept": cid,
                "expected_ancestors": [spine[0]],
            }
        )

    # Interleave buckets so the category is mixed, then pad with broader.
    qs = []
    order = ["sparql", "tagging", "ontology_labels", "mapping_exists", "ontology_broader"]
    idxs = {k: 0 for k in order}
    while len(qs) < target:
        progressed = False
        for k in order:
            if len(qs) >= target:
                break
            i = idxs[k]
            if i < len(buckets[k]):
                qs.append(buckets[k][i])
                idxs[k] = i + 1
                progressed = True
        if not progressed:
            break

    # Final pad with broader / sparql if still short
    for cid in leaves:
        if len(qs) >= target:
            break
        qs.append(
            {
                "id": "TMP",
                "layer": "ontology",
                "question": f"{by_id[cid]['preferred_label']} under {spine[1]} (pad).",
                "type": "ontology_broader",
                "concept": cid,
                "expected_ancestors": [spine[0]],
            }
        )

    return qs[:target]


def expand_map(target, sssom, used):
    qs = []
    for row in sssom:
        if len(qs) >= target:
            break
        qid = f"CQ-MAP-{len(qs)+1:03d}"
        if qid in used:
            # still add with high numbers later via renumber
            pass
        qs.append(
            {
                "id": qid,
                "layer": "mapping",
                "question": f"{row['subject_label'] or row['subject']} → {row['object']}.",
                "type": "mapping_exists",
                "subject": row["subject"],
                "object": row["object"],
            }
        )
    # pad with prefix checks
    prefixes = ["mesh:", "mop:", "GO:", "forest.rule:", "kegg.rclass:", "CHEBI:"]
    for pref in prefixes:
        if len(qs) >= target:
            break
        hit = next((r for r in sssom if r["object"].startswith(pref)), None)
        if not hit:
            continue
        qs.append(
            {
                "id": f"CQ-MAP-{len(qs)+1:03d}",
                "layer": "mapping",
                "question": f"Some concept maps with prefix {pref}.",
                "type": "mapping_exists",
                "subject": hit["subject"],
                "object_prefix": pref,
            }
        )
    return qs[:target]


def renumber(cat, questions):
    out = []
    for i, q in enumerate(questions, 1):
        nq = dict(q)
        nq["id"] = f"CQ-{cat}-{i:03d}"
        out.append(nq)
    return out


def build_gold(by_id, tag_rules, n=150):
    """~10× the prior 15-row gold set."""
    rows = [
        {
            "id": "GOLD-0001",
            "reactant_smiles": "CC",
            "product_smiles": "CCO",
            "tags": "",
            "expected_transformation": "hydroxylation",
            "expected_phase": "phase I",
            "expected_product_class": "",
            "expected_site_environment": "",
            "expected_liability": "metabolic soft spot",
            "expected_external_mapping": "mop:0000673",
        },
        {
            "id": "GOLD-0002",
            "reactant_smiles": "C=C",
            "product_smiles": "C1CO1",
            "tags": "",
            "expected_transformation": "epoxidation",
            "expected_phase": "phase I",
            "expected_product_class": "epoxide",
            "expected_site_environment": "",
            "expected_liability": "bioactivation",
            "expected_external_mapping": "mop:0000671",
        },
        {
            "id": "GOLD-0003",
            "reactant_smiles": "c1ccccc1",
            "product_smiles": "Oc1ccccc1",
            "tags": "chem:aromatic-hydroxylation",
            "expected_transformation": "aromatic hydroxylation",
            "expected_phase": "phase I",
            "expected_product_class": "",
            "expected_site_environment": "",
            "expected_liability": "metabolic soft spot",
            "expected_external_mapping": "",
        },
        {
            "id": "GOLD-0004",
            "reactant_smiles": "CCO",
            "product_smiles": "CCO",
            "tags": "forest.rule:Glucuronidation",
            "expected_transformation": "glucuronidation",
            "expected_phase": "phase II",
            "expected_product_class": "glucuronide conjugate",
            "expected_site_environment": "",
            "expected_liability": "",
            "expected_external_mapping": "",
        },
        {
            "id": "GOLD-0005",
            "reactant_smiles": "[CH3:1]c1ccc([CH3:2])cc1",
            "product_smiles": "O[CH2:1]c1ccc([CH3:2])cc1",
            "tags": "chem:benzylic-hydroxylation@1",
            "expected_transformation": "benzylic hydroxylation",
            "expected_phase": "phase I",
            "expected_product_class": "",
            "expected_site_environment": "benzylic site",
            "expected_liability": "metabolic soft spot",
            "expected_external_mapping": "",
        },
    ]

    # Classify emit labels into gold columns by ancestor spine.
    spine_of = {}
    # rebuild quickly
    doc = yaml.safe_load(YAML_PATH.read_text())
    children = defaultdict(list)
    for c in doc["concepts"]:
        for p in c.get("parents") or []:
            children[p].append(c["id"])

    def under(root):
        return descendants(children, root)

    chem_t = under("xmet:4000213")
    phase1 = under("xmet:4000212") | {"xmet:4000001"} | under("xmet:1200000")
    phase2 = under("xmet:1300000") | {"xmet:4000002"}
    product = under("xmet:1500000")
    site = under("xmet:1600000")
    liability = under("xmet:1400000") | under("xmet:2300000")

    seen_tags = set()

    def add_from_rule(rule, tag):
        if len(rows) >= n:
            return False
        base = tag.split("@", 1)[0]
        if base in seen_tags:
            return False
        seen_tags.add(base)

        transformation = phase = prod = site_e = liab = ""
        for eid, lab in zip(rule["emit"], rule["emit_labels"]):
            if not transformation and eid in chem_t:
                transformation = lab
            if not phase and (eid == "xmet:4000001" or lab == "phase I"):
                phase = "phase I"
            if not phase and (eid == "xmet:4000002" or lab == "phase II"):
                phase = "phase II"
            if not phase and eid in under("xmet:1200000"):
                phase = "phase I"
            if not phase and eid in under("xmet:1300000"):
                phase = "phase II"
            if not prod and eid in product and lab not in (
                "reactive metabolite family",
                "reactive conjugate",
                "stable conjugate",
            ):
                prod = lab
            if not site_e and eid in site and "attachment" not in lab:
                site_e = lab
            if not liab and eid in liability:
                liab = lab

        # Fall back: first primary emit label as transformation
        if not transformation:
            primary = pick_primary_labels(rule["emit_labels"], limit=1)
            if primary:
                transformation = primary[0]

        if not transformation and not prod and not liab and not phase:
            return False

        rows.append(
            {
                "id": f"GOLD-{len(rows)+1:04d}",
                "reactant_smiles": "C",
                "product_smiles": "C",
                "tags": base,
                "expected_transformation": transformation,
                "expected_phase": phase,
                "expected_product_class": prod,
                "expected_site_environment": site_e,
                "expected_liability": liab,
                "expected_external_mapping": "",
            }
        )
        return True

    # Prefer chem: then forest.rule: then forest.pattern:
    for prefer in ("chem:", "forest.rule:", "forest.pattern:"):
        for rule in tag_rules:
            if len(rows) >= n:
                break
            tag = next((t for t in rule["tags"] if t.startswith(prefer)), None)
            if tag:
                add_from_rule(rule, tag)

    return rows[:n]


def main():
    _, by_id, _, children = load()
    sssom = load_sssom()
    tag_rules = load_tag_rules(by_id)

    seeds = seed_questions()
    by_cat = defaultdict(list)
    for q in seeds:
        cat = q["id"].split("-")[1]
        by_cat[cat].append(q)

    # Expand each category to target
    for cat, target in TARGETS.items():
        used = {q["id"] for q in by_cat[cat]}
        if cat == "MAP":
            generated = expand_map(target, sssom, used)
        elif cat in SPINES:
            generated = expand_category(
                cat, target, by_id, children, tag_rules, sssom, used
            )
        else:
            generated = []

        # Merge: keep seeds first, then fill with generated not duplicating seed types heavily
        merged = list(by_cat[cat])
        seed_concepts = {
            q.get("concept") for q in merged if q.get("type") == "ontology_broader"
        }
        seed_tags = set()
        for q in merged:
            if q.get("type") == "tagging":
                for t in q.get("tags") or []:
                    seed_tags.add(t.split("@", 1)[0])

        for q in generated:
            if len(merged) >= target:
                break
            if q.get("type") == "ontology_broader" and q.get("concept") in seed_concepts:
                continue
            if q.get("type") == "tagging":
                t = (q.get("tags") or [""])[0].split("@", 1)[0]
                if t in seed_tags:
                    continue
                seed_tags.add(t)
            merged.append(q)

        # If still short, keep adding broader from remaining leaves
        if cat in SPINES and len(merged) < target:
            spine_id = SPINES[cat][0]
            desc = sorted(descendants(children, spine_id))
            have = {q.get("concept") for q in merged if q.get("type") == "ontology_broader"}
            for cid in desc:
                if len(merged) >= target:
                    break
                if cid in have or cid not in by_id:
                    continue
                merged.append(
                    {
                        "id": "TMP",
                        "layer": "ontology",
                        "question": f"{by_id[cid]['preferred_label']} under {SPINES[cat][1]}.",
                        "type": "ontology_broader",
                        "concept": cid,
                        "expected_ancestors": [spine_id],
                    }
                )

        # P1 also pad with phase-I family broader
        if cat == "P1" and len(merged) < target:
            for cid in sorted(descendants(children, P1_FAMILY)):
                if len(merged) >= target:
                    break
                if cid not in by_id:
                    continue
                merged.append(
                    {
                        "id": "TMP",
                        "layer": "ontology",
                        "question": f"{by_id[cid]['preferred_label']} under phase I reaction family.",
                        "type": "ontology_broader",
                        "concept": cid,
                        "expected_ancestors": [P1_FAMILY],
                    }
                )

        by_cat[cat] = renumber(cat, merged[:target])

    # Assemble in stable category order
    order = ["P1", "P2", "RM", "SITE", "DELTA", "MAP", "EV", "PROV", "LG", "PHARM", "ABOUT", "MED"]
    questions = []
    for cat in order:
        questions.extend(by_cat.get(cat, []))

    out = {
        "version": 3,
        "questions": questions,
    }
    header = (
        "# Executable competency questions for XMET (auto-expanded ~10×).\n"
        "# Regenerated by tools/expand_competency.py — edit seeds there.\n"
        "# Types: ontology_broader, ontology_labels, sparql, shacl,\n"
        "#         mapping_exists, definition_coverage, tagging\n"
    )
    CQ_OUT.write_text(header + yaml.safe_dump(out, sort_keys=False, allow_unicode=True, width=100))

    gold = build_gold(by_id, tag_rules, n=150)
    fields = [
        "id",
        "reactant_smiles",
        "product_smiles",
        "tags",
        "expected_transformation",
        "expected_phase",
        "expected_product_class",
        "expected_site_environment",
        "expected_liability",
        "expected_external_mapping",
    ]
    with GOLD_OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter="\t", lineterminator="\n")
        w.writeheader()
        for row in gold:
            w.writerow(row)

    # summary
    from collections import Counter

    print(f"wrote {CQ_OUT} ({len(questions)} questions)")
    print("  by cat:", dict(Counter(q["id"].split("-")[1] for q in questions)))
    print("  by type:", dict(Counter(q["type"] for q in questions)))
    print(f"wrote {GOLD_OUT} ({len(gold)} rows)")


if __name__ == "__main__":
    main()
