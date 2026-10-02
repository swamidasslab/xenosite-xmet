"""Per-term RDF (Turtle + JSON-LD) sliced from the vocabulary's published graph."""
from __future__ import annotations

import json
from pathlib import Path

from .model import Vocabulary


def write_term_rdf(v: Vocabulary, out_dir: Path) -> int:
    """Write <slug>.ttl and <slug>.jsonld for every concept: its own triples plus
    the labels of the concepts it points to. Returns the number of terms written."""
    from rdflib import Graph, Namespace, URIRef
    from rdflib.namespace import SKOS

    rdf_path = v.cfg.resolve(v.cfg.vocab.get("rdf"))
    if not rdf_path or not rdf_path.exists():
        return 0
    g = Graph(bind_namespaces="none")
    g.parse(rdf_path)
    ns = Namespace(v.cfg.namespace)
    prefixes = dict(g.namespaces())

    out_dir.mkdir(parents=True, exist_ok=True)
    n = 0
    for slug in v.concepts:
        subj = URIRef(v.iri(slug))
        sub = Graph(bind_namespaces="none")
        for pfx, uri in prefixes.items():
            sub.bind(pfx, uri)
        sub.bind(v.cfg.prefix, ns, override=True)
        for _, p, o in g.triples((subj, None, None)):
            sub.add((subj, p, o))
            if isinstance(o, URIRef):
                for lab in g.objects(o, SKOS.prefLabel):
                    sub.add((o, SKOS.prefLabel, lab))
        if not len(sub):
            continue
        (out_dir / f"{slug}.ttl").write_text(sub.serialize(format="turtle"))
        context = {pfx: str(uri) for pfx, uri in sub.namespaces() if pfx}
        doc = json.loads(sub.serialize(format="json-ld", context=context))
        (out_dir / f"{slug}.jsonld").write_text(json.dumps(doc, ensure_ascii=False, indent=2))
        n += 1
    return n
