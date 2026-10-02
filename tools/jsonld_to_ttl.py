#!/usr/bin/env python3
"""Export data/ontology/xmet.skos.jsonld → data/ontology/xmet.ttl.

Full concept graph: SKOS (labels, broader, matches) plus XMET relation
predicates (``relatedTo``, ``suggests``, ``alwaysWith``, ``antonymOf``,
``hasPart`` / ``isPartOf``). Also materializes ``xmet:hasAttachmentAtomType``
when a concept ``skos:relatedMatch`` points at a known attachment-atom site.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JSONLD = ROOT / "data/ontology/xmet.skos.jsonld"
TTL = ROOT / "data/ontology/xmet.ttl"
LEGACY_TTL = ROOT / "data/ontology/xmet-legacy-iris.ttl"

XMET = "https://w3id.org/xenosite/xmet/"
SKOS = "http://www.w3.org/2004/02/skos/core#"
DCT = "http://purl.org/dc/terms/"
# Pre-w3id hash namespace; xmet-legacy-iris.ttl links each old IRI to the new one.
LEGACY_XMET = "https://xenosite.org/ontology/xmet#"

# Well-known CURIE prefixes expanded to full IRIs (others fall back to ext/).
KNOWN_PREFIXES = {"skos": SKOS, "dct": DCT, "dcterms": DCT}

# JSON-LD compact keys → TTL predicate (prefix:local)
SKOS_LINK_PREDS = (
    "broader",
    "narrower",
    "exactMatch",
    "closeMatch",
    "broadMatch",
    "relatedMatch",
)

XMET_LINK_PREDS = (
    ("relatedTo", "xmet:relatedTo"),
    ("suggests", "xmet:suggests"),
    ("alwaysWith", "xmet:alwaysWith"),
    ("operationalizes", "xmet:operationalizes"),
    ("predicts", "xmet:predicts"),
    ("recognizes", "xmet:recognizes"),
    ("enumerates", "xmet:enumerates"),
    ("antonymOf", "xmet:antonymOf"),
    ("hasPart", "dct:hasPart"),
    ("isPartOf", "dct:isPartOf"),
)

# Optional: relatedMatch object → emit hasAttachmentAtomType (post-renumber IDs).
# Empty until attachment-atom site leaves return to the live inventory.
ATTACHMENT: dict[str, str] = {}


def ttl_iri(curie: str) -> str:
    if curie.startswith("xmet:"):
        return f"xmet:{curie.split(':', 1)[1]}"
    if curie.startswith("http://") or curie.startswith("https://"):
        return f"<{curie}>"
    prefix, _, local = curie.partition(":")
    if prefix in KNOWN_PREFIXES and local:
        return f"<{KNOWN_PREFIXES[prefix]}{local}>"
    safe = curie.replace(":", "/")
    return f"<{XMET}ext/{safe}>"


def esc(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def as_list(v):
    if v is None:
        return []
    if isinstance(v, list):
        return v
    return [v]


def write_legacy(data: dict) -> None:
    """owl:sameAs from each pre-w3id hash IRI to its current xmet: IRI."""
    lines = [
        "@prefix owl: <http://www.w3.org/2002/07/owl#> .",
        f"@prefix xmet: <{XMET}> .",
        f"@prefix legacy: <{LEGACY_XMET}> .",
        "",
    ]
    for n in data["@graph"]:
        nid = n["id"]
        if nid.startswith("xmet:"):
            local = nid.split(":", 1)[1]
            lines.append(f"legacy:{local} owl:sameAs xmet:{local} .")
    LEGACY_TTL.write_text("\n".join(lines) + "\n")
    print(f"wrote {LEGACY_TTL}")


def main() -> None:
    data = json.loads(JSONLD.read_text())
    lines = [
        "@prefix skos: <http://www.w3.org/2004/02/skos/core#> .",
        f"@prefix xmet: <{XMET}> .",
        f"@prefix dct: <{DCT}> .",
        "",
    ]
    for n in data["@graph"]:
        nid = n["id"]
        subj = ttl_iri(nid)
        typ = n.get("type", "")
        if typ == "skos:ConceptScheme":
            lines.append(f"{subj} a skos:ConceptScheme ;")
            if n.get("prefLabel"):
                lines.append(f'  skos:prefLabel "{esc(n["prefLabel"])}" ;')
            if n.get("definition"):
                lines.append(f'  skos:definition "{esc(n["definition"])}" ;')
            lines[-1] = lines[-1].rstrip(" ;") + " ."
            lines.append("")
            continue
        if typ != "skos:Concept":
            continue
        stmts = ["a skos:Concept"]
        if n.get("prefLabel"):
            stmts.append(f'skos:prefLabel "{esc(n["prefLabel"])}"')
        if n.get("definition"):
            stmts.append(f'skos:definition "{esc(n["definition"])}"')
        if n.get("inScheme"):
            stmts.append(f"skos:inScheme {ttl_iri(n['inScheme'])}")
        for lab in as_list(n.get("altLabel")):
            stmts.append(f'skos:altLabel "{esc(lab)}"')
        for pred in SKOS_LINK_PREDS:
            for obj in as_list(n.get(pred)):
                stmts.append(f"skos:{pred} {ttl_iri(obj)}")
                if pred == "relatedMatch" and obj in ATTACHMENT:
                    stmts.append(f"xmet:hasAttachmentAtomType {ttl_iri(obj)}")
        for key, ttl_pred in XMET_LINK_PREDS:
            for obj in as_list(n.get(key)):
                stmts.append(f"{ttl_pred} {ttl_iri(obj)}")

        lines.append(f"{subj} {stmts[0]} ;")
        for s in stmts[1:-1]:
            lines.append(f"  {s} ;")
        if len(stmts) > 1:
            lines.append(f"  {stmts[-1]} .")
        else:
            lines[-1] = lines[-1].rstrip(" ;") + " ."
        lines.append("")

    TTL.write_text("\n".join(lines) + "\n")
    write_legacy(data)
    # Drop legacy SKOS-only filename if present
    legacy = ROOT / "data/ontology/xmet.skos.ttl"
    if legacy.exists():
        legacy.unlink()
    print(f"wrote {TTL}")


if __name__ == "__main__":
    main()
