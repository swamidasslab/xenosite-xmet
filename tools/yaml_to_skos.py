#!/usr/bin/env python3
"""Export data/ontology/xmet.yaml → data/ontology/xmet.skos.jsonld."""
from __future__ import annotations

import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
YAML_PATH = ROOT / "data/ontology/xmet.yaml"
SKOS_PATH = ROOT / "data/ontology/xmet.skos.jsonld"

CONTEXT = {
    "skos": "http://www.w3.org/2004/02/skos/core#",
    "dct": "http://purl.org/dc/terms/",
    "xmet": "https://xenosite.org/ontology/xmet#",
    "id": "@id",
    "type": "@type",
    "prefLabel": "skos:prefLabel",
    "altLabel": "skos:altLabel",
    "definition": "skos:definition",
    "broader": {"@id": "skos:broader", "@type": "@id"},
    "narrower": {"@id": "skos:narrower", "@type": "@id"},
    "exactMatch": {"@id": "skos:exactMatch", "@type": "@id"},
    "closeMatch": {"@id": "skos:closeMatch", "@type": "@id"},
    "broadMatch": {"@id": "skos:broadMatch", "@type": "@id"},
    "relatedMatch": {"@id": "skos:relatedMatch", "@type": "@id"},
    "hasPart": {"@id": "dct:hasPart", "@type": "@id"},
    "isPartOf": {"@id": "dct:isPartOf", "@type": "@id"},
    "antonymOf": {"@id": "xmet:antonymOf", "@type": "@id"},
    "relatedTo": {"@id": "xmet:relatedTo", "@type": "@id"},
    "suggests": {"@id": "xmet:suggests", "@type": "@id"},
    "alwaysWith": {"@id": "xmet:alwaysWith", "@type": "@id"},
    "operationalizes": {"@id": "xmet:operationalizes", "@type": "@id"},
    "predicts": {"@id": "xmet:predicts", "@type": "@id"},
    "recognizes": {"@id": "xmet:recognizes", "@type": "@id"},
    "enumerates": {"@id": "xmet:enumerates", "@type": "@id"},
    "inScheme": {"@id": "skos:inScheme", "@type": "@id"},
}


def one_or_list(vals):
    if not vals:
        return None
    if len(vals) == 1:
        return vals[0]
    return vals


def main():
    doc = yaml.safe_load(YAML_PATH.read_text())
    scheme = doc["scheme"]
    graph = [
        {
            "id": scheme["id"],
            "type": "skos:ConceptScheme",
            "prefLabel": scheme.get("preferred_label"),
            "iri": scheme.get("iri"),
            "definition": scheme.get("definition"),
        }
    ]
    for c in doc["concepts"]:
        node = {
            "id": c["id"],
            "type": "skos:Concept",
            "prefLabel": c["preferred_label"],
            "inScheme": "xmet:scheme",
        }
        if c.get("definition"):
            node["definition"] = c["definition"]
        if c.get("synonyms"):
            node["altLabel"] = c["synonyms"]
        parents = c.get("parents") or []
        if parents:
            node["broader"] = one_or_list(parents)
        for src, dst in [
            ("exact_match", "exactMatch"),
            ("close_match", "closeMatch"),
            ("related_match", "relatedMatch"),
            ("broad_match", "broadMatch"),
            ("has_part", "hasPart"),
            ("is_part_of", "isPartOf"),
            ("antonyms", "antonymOf"),
            ("related_to", "relatedTo"),
            ("suggests", "suggests"),
            ("always_with", "alwaysWith"),
            ("operationalizes", "operationalizes"),
            ("predicts", "predicts"),
            ("recognizes", "recognizes"),
            ("enumerates", "enumerates"),
        ]:
            if c.get(src):
                node[dst] = one_or_list(c[src])
        if c.get("id") == "xmet:4000000":
            node["topConcept"] = True
        graph.append(node)
    # scheme first already; ensure root second
    root = next(n for n in graph if n["id"] == "xmet:4000000")
    others = [n for n in graph if n["id"] not in ("xmet:scheme", "xmet:4000000")]
    others.sort(key=lambda n: n["id"])
    out = {"@context": CONTEXT, "@graph": [graph[0], root, *others]}
    SKOS_PATH.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {SKOS_PATH} ({len(others)+1} concepts)")


if __name__ == "__main__":
    main()
