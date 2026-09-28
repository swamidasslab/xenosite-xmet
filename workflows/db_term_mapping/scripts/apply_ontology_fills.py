#!/usr/bin/env python3
"""Mint XMET concepts to close DB mapping gaps and wire antonym related_match links.

Uses ruamel.yaml round-trip to preserve existing authoring structure.

Usage (from repo root):
  uv run python workflows/db_term_mapping/scripts/apply_ontology_fills.py
  uv run python tools/yaml_to_skos.py
"""
from __future__ import annotations

import sys
from pathlib import Path

from ruamel.yaml import YAML

REPO = Path(__file__).resolve().parents[3]
YAML_PATH = REPO / "data/ontology/xmet.yaml"
REPORT = REPO / "data/derived/db_term_mapping/ontology_fills_report.tsv"

# Import fill definitions from sibling module constants by exec-safe duplicate:
# keep FILLS inline below (same as previous).

FILLS: list[dict] = [
    {
        "id": "xmet:1500230",
        "preferred_label": "macromolecule binding",
        "synonyms": ["macromolecular adduct formation", "covalent macromolecule binding"],
        "definition": "Reactive-metabolite outcome: covalent or tight binding to biological macromolecules.",
        "parents": ["xmet:1500000"],
    },
    {
        "id": "xmet:1500231",
        "preferred_label": "DNA binding",
        "synonyms": ["DNA adduct formation", "nucleic acid binding", "DNA adduct"],
        "definition": "Reactive metabolite binding/adduct formation on DNA (AMD RXNCLASS in scope).",
        "parents": ["xmet:1500230", "xmet:1500000"],
    },
    {
        "id": "xmet:1500232",
        "preferred_label": "RNA binding",
        "synonyms": ["RNA adduct"],
        "definition": "Reactive metabolite binding/adduct formation on RNA.",
        "parents": ["xmet:1500230"],
    },
    {
        "id": "xmet:1500233",
        "preferred_label": "protein binding",
        "synonyms": ["protein adduct formation", "protein adduct"],
        "definition": "Reactive metabolite binding/adduct formation on protein (AMD RXNCLASS in scope).",
        "parents": ["xmet:1500230", "xmet:1500000"],
    },
    {
        "id": "xmet:1500234",
        "preferred_label": "covalent binding",
        "synonyms": ["covalent adduct formation", "covalent macromolecule adduct"],
        "definition": "Generic covalent binding of a reactive metabolite to biomolecules.",
        "parents": ["xmet:1500230", "xmet:1500000"],
        "related_match": ["xmet:1500231", "xmet:1500233"],
    },
    {
        "id": "xmet:1500235",
        "preferred_label": "lipid binding",
        "synonyms": ["lipid adduct"],
        "definition": "Reactive metabolite binding to lipids.",
        "parents": ["xmet:1500230"],
    },
    {
        "id": "xmet:1500236",
        "preferred_label": "CoA binding",
        "synonyms": ["acyl-CoA adduct", "CoA adduct"],
        "definition": "Binding/adduct involving coenzyme A (often acyl-CoA related).",
        "parents": ["xmet:1500230"],
        "related_match": ["xmet:4000185"],
    },
    {
        "id": "xmet:4000114",
        "preferred_label": "cyanidation",
        "synonyms": ["cyano addition", "nitrile formation", "cyanide incorporation"],
        "definition": "Introduction of a cyano/cyanide group (reactive/toxicophore-relevant).",
        "parents": ["xmet:4000213"],
        "related_match": ["xmet:4000257", "xmet:1500000"],
    },
    {
        "id": "xmet:4000115",
        "preferred_label": "decyanidation",
        "synonyms": ["cyano loss", "nitrile cleavage", "cyanide release"],
        "definition": "Loss/cleavage of a cyano/cyanide group. Antonym of cyanidation.",
        "parents": ["xmet:4000213"],
        "related_match": ["xmet:4000114", "xmet:4000086", "xmet:4000257"],
    },
    {
        "id": "xmet:4000116",
        "preferred_label": "alkylation",
        "synonyms": ["alkyl transfer", "alkyl conjugation"],
        "definition": "Addition of an alkyl group. Antonym of dealkylation.",
        "parents": ["xmet:4000213"],
        "related_match": ["xmet:4000042"],
    },
    {
        "id": "xmet:4000117",
        "preferred_label": "N-alkylation",
        "synonyms": ["nitrogen alkylation"],
        "definition": "Alkylation at nitrogen. Antonym of N-dealkylation.",
        "parents": ["xmet:4000116"],
        "related_match": ["xmet:4000043"],
    },
    {
        "id": "xmet:4000118",
        "preferred_label": "O-alkylation",
        "synonyms": ["oxygen alkylation", "ether formation"],
        "definition": "Alkylation at oxygen. Antonym of O-dealkylation.",
        "parents": ["xmet:4000116"],
        "related_match": ["xmet:4000044"],
    },
    {
        "id": "xmet:4000119",
        "preferred_label": "S-alkylation",
        "synonyms": ["sulfur alkylation", "thioether formation"],
        "definition": "Alkylation at sulfur. Antonym of S-dealkylation.",
        "parents": ["xmet:4000116"],
        "related_match": ["xmet:4000045"],
    },
    {
        "id": "xmet:4000120",
        "preferred_label": "C-alkylation",
        "synonyms": ["carbon alkylation"],
        "definition": "Alkylation at carbon. Antonym of C-dealkylation.",
        "parents": ["xmet:4000116"],
        "related_match": ["xmet:4000046"],
    },
    {
        "id": "xmet:4000121",
        "preferred_label": "decarboxylation",
        "synonyms": ["CO2 loss", "carboxyl loss", "C-decarboxylation"],
        "definition": "Loss of CO2 from a carboxylic acid (distinct from decarbonylation).",
        "parents": ["xmet:4000213"],
        "related_match": ["xmet:4000193"],
    },
    {
        "id": "xmet:4000122",
        "preferred_label": "carboxylation",
        "synonyms": ["CO2 addition", "carboxyl formation"],
        "definition": "Introduction of a carboxyl group. Antonym of decarboxylation.",
        "parents": ["xmet:4000213"],
        "related_match": ["xmet:4000121"],
    },
    {
        "id": "xmet:4000123",
        "preferred_label": "esterification",
        "synonyms": ["ester formation"],
        "definition": "Formation of an ester. Antonym of ester hydrolysis.",
        "parents": ["xmet:4000213"],
        "related_match": ["xmet:4000078"],
    },
    {
        "id": "xmet:4000124",
        "preferred_label": "transesterification",
        "synonyms": ["ester exchange"],
        "definition": "Exchange of ester alkoxy groups.",
        "parents": ["xmet:4000213"],
        "related_match": ["xmet:4000123", "xmet:4000078"],
    },
    {
        "id": "xmet:4000125",
        "preferred_label": "lactonization",
        "synonyms": ["lactone formation", "intramolecular esterification"],
        "definition": "Intramolecular ester formation to a lactone. Antonym of lactone hydrolysis.",
        "parents": ["xmet:4000213"],
        "related_match": ["xmet:4000080", "xmet:4000123"],
    },
    {
        "id": "xmet:4000126",
        "preferred_label": "lactamization",
        "synonyms": ["lactam formation", "intramolecular amidation"],
        "definition": "Intramolecular amide formation to a lactam. Antonym of lactam hydrolysis.",
        "parents": ["xmet:4000213"],
        "related_match": ["xmet:4000081"],
    },
    {
        "id": "xmet:4000127",
        "preferred_label": "cyclization",
        "synonyms": ["ring-forming cyclization", "annulation"],
        "definition": "Formation of a new ring by cyclization.",
        "parents": ["xmet:4000213", "xmet:0004000"],
    },
    {
        "id": "xmet:4000128",
        "preferred_label": "dehydroxylation",
        "synonyms": ["dehydroxy", "OH loss", "aromatic dehydroxylation", "N-dehydroxylation"],
        "definition": "Loss of a hydroxyl group. Antonym of hydroxylation.",
        "parents": ["xmet:4000213"],
        "related_match": ["xmet:4000012"],
    },
    {
        "id": "xmet:4000129",
        "preferred_label": "halogenation",
        "synonyms": ["halide addition"],
        "definition": "Introduction of halogen. Antonym of dehalogenation.",
        "parents": ["xmet:4000213"],
        "related_match": ["xmet:4000214"],
    },
    {
        "id": "xmet:4000130",
        "preferred_label": "amination",
        "synonyms": ["amino group introduction"],
        "definition": "Introduction of an amino group. Antonym of deamination.",
        "parents": ["xmet:4000213"],
        "related_match": ["xmet:4000049"],
    },
    {
        "id": "xmet:4000131",
        "preferred_label": "formylation",
        "synonyms": ["N-formylation", "formyl conjugation"],
        "definition": "Introduction of a formyl group (often N-formylation).",
        "parents": ["xmet:4000213", "xmet:1300000"],
        "related_match": ["xmet:4000163"],
    },
    {
        "id": "xmet:4000132",
        "preferred_label": "deformylation",
        "synonyms": ["N-deformylation", "formyl loss"],
        "definition": "Loss of a formyl group. Antonym of formylation.",
        "parents": ["xmet:4000213"],
        "related_match": ["xmet:4000131"],
    },
    {
        "id": "xmet:4000133",
        "preferred_label": "N-nitrosation",
        "synonyms": ["nitrosation", "N-nitroso formation"],
        "definition": "Formation of an N-nitroso species (reactive-metabolite relevant).",
        "parents": ["xmet:4000213", "xmet:1500000"],
        "related_match": ["xmet:4000029", "xmet:1500110"],
    },
    {
        "id": "xmet:4000135",
        "preferred_label": "desulfuration",
        "synonyms": ["oxidative desulfuration", "desulfurization", "P=S to P=O"],
        "definition": "Removal/replacement of sulfur (e.g. phosphorothioate oxidative desulfuration).",
        "parents": ["xmet:4000213"],
        "related_match": ["xmet:4000032"],
    },
    {
        "id": "xmet:4000136",
        "preferred_label": "sulfuration",
        "synonyms": ["thionation", "S introduction"],
        "definition": "Introduction of sulfur. Antonym of desulfuration (not synonymous with sulfation).",
        "parents": ["xmet:4000213"],
        "related_match": ["xmet:4000135"],
    },
    {
        "id": "xmet:4000137",
        "preferred_label": "deglucuronidation",
        "synonyms": ["O-deglucuronidation", "glucuronide hydrolysis"],
        "definition": "Hydrolytic removal of a glucuronide. Antonym of glucuronidation.",
        "parents": ["xmet:4000213", "xmet:4000007"],
        "related_match": ["xmet:4000148", "xmet:4000149"],
    },
    {
        "id": "xmet:4000138",
        "preferred_label": "desulfation",
        "synonyms": ["sulfate hydrolysis", "O-desulfation"],
        "definition": "Hydrolytic removal of a sulfate. Antonym of sulfation.",
        "parents": ["xmet:4000213", "xmet:4000007"],
        "related_match": ["xmet:4000158", "xmet:4000159"],
    },
    {
        "id": "xmet:4000139",
        "preferred_label": "deglycosidation",
        "synonyms": [
            "O-deglycosidation",
            "N-deglycosidation",
            "deglucosidation",
            "glycoside hydrolysis",
        ],
        "definition": "Cleavage of a glycoside. Antonym of glycosylation.",
        "parents": ["xmet:4000213", "xmet:4000007"],
        "related_match": ["xmet:4000184", "xmet:4000084"],
    },
    {
        "id": "xmet:4000140",
        "preferred_label": "deglutathionation",
        "synonyms": ["GSH adduct cleavage", "glutathione adduct hydrolysis"],
        "definition": "Removal of a glutathione adduct. Antonym of glutathionation.",
        "parents": ["xmet:4000213"],
        "related_match": ["xmet:4000167"],
    },
    {
        "id": "xmet:4000141",
        "preferred_label": "decysteination",
        "synonyms": ["cysteine adduct cleavage"],
        "definition": "Removal of a cysteine conjugate. Antonym of cysteine conjugation.",
        "parents": ["xmet:4000213"],
        "related_match": ["xmet:4000217"],
    },
    {
        "id": "xmet:4000142",
        "preferred_label": "Se-methylation",
        "synonyms": ["selenium methylation"],
        "definition": "Methylation at selenium (distinct from S-methylation).",
        "parents": ["xmet:4000175"],
        "related_match": ["xmet:4000178"],
    },
    {
        "id": "xmet:4000143",
        "preferred_label": "dearylation",
        "synonyms": ["O-dearylation", "N-dearylation", "aryl ether cleavage"],
        "definition": "Cleavage removing an aryl group from N/O/S (related to dealkylation).",
        "parents": ["xmet:4000042"],
        "related_match": ["xmet:4000043", "xmet:4000044"],
    },
    {
        "id": "xmet:4000144",
        "preferred_label": "alpha-hydroxylation",
        "synonyms": ["α-hydroxylation", "alpha hydroxylation of carbonyl"],
        "definition": "Hydroxylation at a carbon alpha to a carbonyl or heteroatom.",
        "parents": ["xmet:4000012"],
        "related_match": ["xmet:4000014"],
    },
    {
        "id": "xmet:1600200",
        "preferred_label": "alicyclic site",
        "synonyms": ["alicyclic carbon", "cycloalkyl site"],
        "definition": "Site on an alicyclic (saturated ring) carbon.",
        "parents": ["xmet:1600000"],
    },
    {
        "id": "xmet:1600201",
        "preferred_label": "fused benzene site",
        "synonyms": ["fused aromatic ring site"],
        "definition": "Aromatic carbon on a fused benzene ring system.",
        "parents": ["xmet:1600004"],
    },
]

ANTONYM_PAIRS = [
    ("xmet:4000042", "xmet:4000116"),
    ("xmet:4000043", "xmet:4000117"),
    ("xmet:4000044", "xmet:4000118"),
    ("xmet:4000045", "xmet:4000119"),
    ("xmet:4000046", "xmet:4000120"),
    ("xmet:4000012", "xmet:4000128"),
    ("xmet:4000148", "xmet:4000137"),
    ("xmet:4000149", "xmet:4000137"),
    ("xmet:4000158", "xmet:4000138"),
    ("xmet:4000159", "xmet:4000138"),
    ("xmet:4000184", "xmet:4000139"),
    ("xmet:4000167", "xmet:4000140"),
    ("xmet:4000217", "xmet:4000141"),
    ("xmet:4000114", "xmet:4000115"),
    ("xmet:4000121", "xmet:4000122"),
    ("xmet:4000131", "xmet:4000132"),
    ("xmet:4000135", "xmet:4000136"),
    ("xmet:4000078", "xmet:4000123"),
    ("xmet:4000080", "xmet:4000125"),
    ("xmet:4000081", "xmet:4000126"),
    ("xmet:4000214", "xmet:4000129"),
    ("xmet:4000049", "xmet:4000130"),
]


def ensure_related(concept: dict, other_id: str) -> None:
    rel = concept.get("related_match")
    if rel is None:
        concept["related_match"] = [other_id]
        return
    if other_id not in list(rel):
        rel.append(other_id)


def main() -> int:
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.width = 100
    doc = yaml.load(YAML_PATH.read_text())
    concepts = doc["concepts"]
    index = {c["id"]: c for c in concepts}

    rows = []
    for fill in FILLS:
        cid = fill["id"]
        if cid in index:
            existing = index[cid]
            syns = list(existing.get("synonyms") or [])
            for s in fill.get("synonyms") or []:
                if s not in syns:
                    syns.append(s)
            if syns:
                existing["synonyms"] = syns
            for r in fill.get("related_match") or []:
                ensure_related(existing, r)
            rows.append((cid, fill["preferred_label"], "exists_merged"))
            continue
        concepts.append(dict(fill))
        index[cid] = concepts[-1]
        rows.append((cid, fill["preferred_label"], "added"))

    index = {c["id"]: c for c in concepts}
    for a, b in ANTONYM_PAIRS:
        if a in index and b in index:
            ensure_related(index[a], b)
            ensure_related(index[b], a)

    yaml.dump(doc, YAML_PATH)

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        "xrm_id\tpreferred_label\tstatus\n"
        + "\n".join(f"{i}\t{p}\t{s}" for i, p, s in rows)
        + "\n"
    )
    added = sum(1 for *_, s in rows if s == "added")
    print(f"[ontology_fills] added={added} merged={len(rows)-added} → {YAML_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
