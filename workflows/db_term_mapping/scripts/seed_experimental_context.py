#!/usr/bin/env python3
"""Seed experimental-context terminology under biological context.

Adds experimental setting / assay-system branches, missing species and assay
leaves (baculosomes, S9, …), reparents key existing tissue/species/matrix
leaves under their branch roots, and writes a starter
reaction↔context expectation table (inheritance + exclusions).

Usage (repo root):
  uv run python workflows/db_term_mapping/scripts/seed_experimental_context.py
  uv run python tools/yaml_to_skos.py
"""
from __future__ import annotations

from pathlib import Path

from ruamel.yaml import YAML

REPO = Path(__file__).resolve().parents[3]
YAML_PATH = REPO / "data/ontology/xmet.yaml"
EXPECT_PATH = (
    REPO / "data/mappings/xmet-reaction-context-expectations.tsv"
)

BRANCHES = [
    {
        "id": "xmet:2100300",
        "preferred_label": "experimental setting",
        "synonyms": ["study setting", "in vivo vs in vitro framing"],
        "definition": (
            "Whether observations come from an in-vivo organism study or an "
            "in-vitro experimental system. Orthogonal to tissue, species, matrix, "
            "and assay system."
        ),
        "parents": ["xmet:2100000"],
    },
    {
        "id": "xmet:2100301",
        "preferred_label": "in vivo setting",
        "synonyms": ["in vivo", "whole-animal study"],
        "definition": "In-vivo experimental setting (metabolites often reported in plasma, urine, bile, feces, tissues).",
        "parents": ["xmet:2100300"],
        "related_match": ["xmet:2000112"],
    },
    {
        "id": "xmet:2100302",
        "preferred_label": "in vitro setting",
        "synonyms": ["in vitro", "ex vivo incubation"],
        "definition": "In-vitro / ex-vivo experimental setting (cells, subcellular fractions, recombinants).",
        "parents": ["xmet:2100300"],
        "related_match": ["xmet:2000111"],
    },
    {
        "id": "xmet:2100310",
        "preferred_label": "assay system",
        "synonyms": ["incubation system", "metabolism assay system"],
        "definition": (
            "Experimental assay system used to generate or detect metabolites "
            "(hepatocytes, microsomes, baculosomes/recombinants, S9, …)."
        ),
        "parents": ["xmet:2100000", "xmet:2100302"],
    },
]

LEAVES = [
    # assay systems
    {
        "id": "xmet:2100311",
        "preferred_label": "hepatocyte assay",
        "synonyms": ["hepatocytes", "primary hepatocytes", "hepatocyte incubation system"],
        "definition": "Intact hepatocyte incubation (Phase I + II competent when fresh/cryopreserved).",
        "parents": ["xmet:2100310", "xmet:2100125"],
        "related_match": ["xmet:2000018", "xmet:2000120", "xmet:2100109"],
    },
    {
        "id": "xmet:2100312",
        "preferred_label": "microsome assay",
        "synonyms": ["microsomes", "liver microsomes", "HLM", "RLM"],
        "definition": "Microsomal fraction incubation (ER enzymes: CYPs, UGTs, FMOs, …).",
        "parents": ["xmet:2100310", "xmet:2100123"],
        "related_match": ["xmet:2000119"],
    },
    {
        "id": "xmet:2100313",
        "preferred_label": "baculosome assay",
        "synonyms": ["baculosomes", "Baculovirus insect-cell membranes", "insect-cell recombinant membranes"],
        "definition": "Baculovirus/insect-cell expressed enzyme membrane preparations (often single CYP/UGT).",
        "parents": ["xmet:2100310", "xmet:2100220"],
        "related_match": ["xmet:2100221"],
    },
    {
        "id": "xmet:2100314",
        "preferred_label": "S9 assay",
        "synonyms": ["S9 fraction", "liver S9"],
        "definition": "Post-mitochondrial S9 fraction (microsomes + cytosol enzymes).",
        "parents": ["xmet:2100310"],
        "related_match": ["xmet:2000118"],
    },
    {
        "id": "xmet:2100315",
        "preferred_label": "cytosol assay",
        "synonyms": ["cytosolic fraction", "liver cytosol"],
        "definition": "Cytosolic fraction incubation (SULTs, NATs, GSTs, AO partly, …).",
        "parents": ["xmet:2100310", "xmet:2100124"],
    },
    {
        "id": "xmet:2100316",
        "preferred_label": "tissue slice assay",
        "synonyms": ["precision-cut tissue slices", "liver slices"],
        "definition": "Precision-cut tissue slice incubations.",
        "parents": ["xmet:2100310"],
    },
    {
        "id": "xmet:2100317",
        "preferred_label": "homogenate assay",
        "synonyms": ["tissue homogenate incubation"],
        "definition": "Crude tissue homogenate incubation.",
        "parents": ["xmet:2100310", "xmet:2100219"],
    },
    {
        "id": "xmet:2100318",
        "preferred_label": "recombinant enzyme assay",
        "synonyms": ["rCYP", "recombinant CYP/UGT", "Supersomes"],
        "definition": "Purified or membrane-bound recombinant enzyme incubations (incl. Supersomes).",
        "parents": ["xmet:2100310", "xmet:2100220", "xmet:2100221"],
    },
    # species gaps from AMD basics
    {
        "id": "xmet:2100320",
        "preferred_label": "guinea pig species context",
        "synonyms": ["guinea pig", "cavia"],
        "definition": "Guinea pig species framing (common metabolism species).",
        "parents": ["xmet:2100012"],
    },
    {
        "id": "xmet:2100321",
        "preferred_label": "pig species context",
        "synonyms": ["pig", "swine", "porcine"],
        "definition": "Pig / porcine species framing.",
        "parents": ["xmet:2100012"],
    },
    {
        "id": "xmet:2100322",
        "preferred_label": "hamster species context",
        "synonyms": ["hamster"],
        "definition": "Hamster species framing.",
        "parents": ["xmet:2100012"],
    },
    {
        "id": "xmet:2100323",
        "preferred_label": "cynomolgus monkey species context",
        "synonyms": ["cynomolgus", "Macaca fascicularis", "cyno"],
        "definition": "Cynomolgus monkey (common NHP metabolism species).",
        "parents": ["xmet:2100012", "xmet:2100118"],
    },
]

# Reparent existing leaves under branch roots (keep prior parents if useful)
REPARENT = {
    # tissues → tissue context
    "xmet:2100109": ["xmet:2100011"],  # liver
    "xmet:2100110": ["xmet:2100011"],  # intestine
    "xmet:2100111": ["xmet:2100011"],  # kidney
    "xmet:2100112": ["xmet:2100011"],  # lung
    "xmet:2100113": ["xmet:2100011"],  # brain
    "xmet:2100212": ["xmet:2100011"],  # skin
    "xmet:2100213": ["xmet:2100011"],  # placenta
    "xmet:2100214": ["xmet:2100011"],  # adrenal
    # species → species context
    "xmet:2100114": ["xmet:2100012"],
    "xmet:2100115": ["xmet:2100012"],
    "xmet:2100116": ["xmet:2100012"],
    "xmet:2100117": ["xmet:2100012"],
    "xmet:2100118": ["xmet:2100012"],
    "xmet:2100215": ["xmet:2100012"],
    "xmet:2100216": ["xmet:2100012"],
    # matrices → matrix context (+ in vivo setting for excretory matrices)
    "xmet:2100119": ["xmet:2100013", "xmet:2100301"],  # plasma
    "xmet:2100120": ["xmet:2100013", "xmet:2100301"],  # urine
    "xmet:2100121": ["xmet:2100013", "xmet:2100301"],  # bile
    "xmet:2100122": ["xmet:2100013", "xmet:2100301"],  # feces
    "xmet:2100217": ["xmet:2100013", "xmet:2100301"],  # serum
    "xmet:2100218": ["xmet:2100013", "xmet:2100301"],  # whole blood
    # assay matrices → assay system + matrix
    "xmet:2100123": ["xmet:2100013", "xmet:2100310"],  # microsome matrix
    "xmet:2100124": ["xmet:2100013", "xmet:2100310"],  # cytosol
    "xmet:2100125": ["xmet:2100013", "xmet:2100310"],  # hepatocyte matrix
    "xmet:2100219": ["xmet:2100013", "xmet:2100310"],  # homogenate
    "xmet:2100220": ["xmet:2100013", "xmet:2100310"],  # recombinant
    "xmet:2100221": ["xmet:2100013", "xmet:2100310"],  # supersome
}

# Starter expectations: reaction class → context
# relation: likely_in | observed_in | unlikely_in
# inherit_children: true applies to skos:narrower descendants unless excluded
EXPECTATIONS = [
    # header documented in file
    ("xmet:4000009", "xmet:2100312", "likely_in", "true", "", "Oxidative metabolism common in microsomes"),
    ("xmet:4000009", "xmet:2100311", "likely_in", "true", "", "Oxidative metabolism common in hepatocytes"),
    ("xmet:4000009", "xmet:2100318", "likely_in", "true", "", "rCYP/Supersomes/baculosomes for CYP oxidations"),
    ("xmet:4000009", "xmet:2100313", "likely_in", "true", "", "Baculosome CYP panels"),
    ("xmet:4000012", "xmet:2100312", "likely_in", "true", "", "Hydroxylation in microsomes"),
    ("xmet:4000012", "xmet:2100311", "likely_in", "true", "", "Hydroxylation in hepatocytes"),
    ("xmet:4000042", "xmet:2100312", "likely_in", "true", "", "Oxidative dealkylation in microsomes"),
    ("xmet:4000148", "xmet:2100311", "likely_in", "true", "", "Glucuronidation in hepatocytes (UGT)"),
    ("xmet:4000148", "xmet:2100312", "likely_in", "true", "xmet:4000152", "Microsomal UGTs; acyl glucuronidation often called out separately"),
    ("xmet:4000148", "xmet:2100120", "observed_in", "true", "", "Glucuronides frequently recovered in urine"),
    ("xmet:4000148", "xmet:2100119", "observed_in", "true", "", "Glucuronides in plasma"),
    ("xmet:4000148", "xmet:2100301", "likely_in", "true", "", "Phase II conjugates common in vivo"),
    ("xmet:4000158", "xmet:2100315", "likely_in", "true", "", "Sulfation primarily cytosolic"),
    ("xmet:4000158", "xmet:2100311", "likely_in", "true", "", "Hepatocytes retain SULT activity"),
    ("xmet:4000158", "xmet:2100312", "unlikely_in", "true", "", "Classical microsomes lack SULTs"),
    ("xmet:4000167", "xmet:2100311", "likely_in", "true", "", "GSH conjugation in hepatocytes"),
    ("xmet:4000167", "xmet:2100315", "likely_in", "true", "", "Cytosolic GSTs"),
    ("xmet:4000007", "xmet:2100311", "likely_in", "true", "", "Hydrolysis in hepatocytes"),
    ("xmet:4000007", "xmet:2100312", "likely_in", "true", "", "CES etc. in microsomes"),
    ("xmet:4000007", "xmet:2100119", "observed_in", "true", "", "Ester hydrolysis also in plasma"),
    ("xmet:4000163", "xmet:2100315", "likely_in", "true", "", "NAT acetylation cytosolic"),
    ("xmet:4000163", "xmet:2100312", "unlikely_in", "true", "", "Not typical microsomal"),
]


def ensure_list_field(concept: dict, key: str) -> list:
    val = concept.get(key)
    if val is None:
        concept[key] = []
        return concept[key]
    if not isinstance(val, list):
        concept[key] = [val]
        return concept[key]
    return val


def add_or_merge(doc: dict, index: dict, concept: dict) -> str:
    cid = concept["id"]
    if cid in index:
        existing = index[cid]
        syns = ensure_list_field(existing, "synonyms") if concept.get("synonyms") else []
        if concept.get("synonyms"):
            syns = ensure_list_field(existing, "synonyms")
            for s in concept["synonyms"]:
                if s not in syns:
                    syns.append(s)
        if concept.get("related_match"):
            rel = ensure_list_field(existing, "related_match")
            for r in concept["related_match"]:
                if r not in rel:
                    rel.append(r)
        if concept.get("parents"):
            parents = ensure_list_field(existing, "parents")
            for p in concept["parents"]:
                if p not in parents:
                    parents.append(p)
        return "merged"
    doc["concepts"].append(dict(concept))
    index[cid] = doc["concepts"][-1]
    return "added"


def main() -> int:
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.width = 100
    doc = yaml.load(YAML_PATH.read_text())
    index = {c["id"]: c for c in doc["concepts"]}

    stats = {"added": 0, "merged": 0}
    for c in BRANCHES + LEAVES:
        st = add_or_merge(doc, index, c)
        stats["added" if st == "added" else "merged"] += 1

    index = {c["id"]: c for c in doc["concepts"]}
    for cid, parents in REPARENT.items():
        if cid not in index:
            continue
        # Replace flat biological-context-only parent with branch parents
        cur = list(index[cid].get("parents") or [])
        # drop bare spine root if we're attaching to a branch
        new_parents = [p for p in cur if p != "xmet:2100000"]
        for p in parents:
            if p not in new_parents:
                new_parents.append(p)
        index[cid]["parents"] = new_parents

    # Synonyms on existing species from AMD casing
    for cid, syns in {
        "xmet:2100114": ["Human", "human"],
        "xmet:2100115": ["Rat", "rat"],
        "xmet:2100116": ["Mouse", "mouse"],
        "xmet:2100117": ["Dog", "dog"],
        "xmet:2100118": ["Monkey", "monkey", "non-human primate"],
        "xmet:2100125": ["hepatocytes"],
        "xmet:2100123": ["microsomes", "liver microsomes"],
        "xmet:2100221": ["Supersomes", "baculosome-related recombinant membranes"],
    }.items():
        if cid not in index:
            continue
        cur = ensure_list_field(index[cid], "synonyms")
        for s in syns:
            if s not in cur:
                cur.append(s)

    yaml.dump(doc, YAML_PATH)

    EXPECT_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "reaction_id\tcontext_id\trelation\tinherit_children\texclude_reaction_ids\tnote",
        "# relation: likely_in | observed_in | unlikely_in",
        "# inherit_children=true → applies to skos:narrower descendants except exclude_reaction_ids (pipe-separated)",
        "# This is an expectation / prior for systems biology annotation — not a hard axiom.",
    ]
    for row in EXPECTATIONS:
        lines.append("\t".join(row))
    EXPECT_PATH.write_text("\n".join(lines) + "\n")

    print(f"[experimental_context] ontology {stats} → {YAML_PATH}")
    print(f"[experimental_context] expectations {len(EXPECTATIONS)} → {EXPECT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
