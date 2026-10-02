# xenosite-xmet

**XMET** — xenobiotic metabolism SKOS thesaurus and ontology tooling for
[xenosite](https://xenosite.org).

This repo is the **source of truth** for the XMET concept scheme: authoring YAML,
exported SKOS, SSSOM crosswalks, competency questions, and MetXBioDB/AMD
term→XMET mapping. Concept CURIEs use the `xmet:` prefix (e.g. `xmet:4000213`).
Namespace: `https://w3id.org/xenosite/xmet/` — concept IRIs are
`https://w3id.org/xenosite/xmet/4000213`, scheme `…/xmet/scheme`. Pre-w3id hash
IRIs (`https://xenosite.org/ontology/xmet#…`) are linked by `owl:sameAs` in
[`data/ontology/xmet-legacy-iris.ttl`](data/ontology/xmet-legacy-iris.ttl).

The reaction **tagger / RuleSet engine** lives in
[`swamidasslab/xenosite-tagger`](https://github.com/swamidasslab/xenosite-tagger),
which vendors this repository as a **git submodule**. XMET does **not** own
RuleSet YAML or rule-bridge scripts. SSSOM mapping *data* lives here; scripts
that build or test mappings stay in tagger and may push updates into this repo
later.

[xenosite.org](https://xenosite.org) · MIT

## What this is

| Piece | Role |
| --- | --- |
| `data/ontology/xmet.yaml` | Authoring thesaurus (edit this) |
| `data/ontology/xmet.skos.jsonld` | Runtime SKOS for the Rust namer |
| `data/mappings/*.sssom.tsv` | Crosswalks to RXNO/MOP/MeSH/GO/Forest/… |
| `data/competency/` | CQs, SPARQL, fixtures, gold set |
| `tools/` | YAML→SKOS, stats, extractors, harvest |
| `workflows/db_term_mapping/` | MetXBioDB / AMD label → XMET |

XMET is a med-chem naming thesaurus for xenobiotic metabolism — **not** an
extension of RXNO, MOP, GO, or KEGG. Those are mapping targets. See
[`data/ontology/SCOPE.md`](data/ontology/SCOPE.md) and
[`RELATED_ONTOLOGIES.md`](data/ontology/RELATED_ONTOLOGIES.md).

## Setup (standalone)

```bash
git clone git@github.com:swamidasslab/xenosite-xmet.git
cd xenosite-xmet
uv sync

make ontology-export    # regenerate JSON-LD + xmet.ttl (SKOS + xmet: relations) from xmet.yaml
make ontology-stats     # spine / mapping inventory
make db-term-mapping    # requires local MetX/AMD extracts under data/
```

Python package: `xenosite.xmet` (namespace package; path helpers only).

```python
from xenosite.xmet import ontology_yaml, data_dir
```

## Used as a tagger submodule

Tagger clones this repo at `xenosite-xmet/`:

```bash
git clone --recurse-submodules git@github.com:swamidasslab/xenosite-tagger.git
```

From the tagger root, the same Make targets are wrapped (`make ontology-export`,
etc.). After you commit ontology changes here, bump the submodule pin in tagger.

## Layout

```
xenosite-xmet/
├── data/ontology/          # xmet.yaml + SKOS/TTL/SHACL + docs
├── data/mappings/          # SSSOM TSV (+ views/)
├── data/competency/        # CQ YAML, SPARQL, gold fixtures
├── data/candidates/        # harvest / coverage artifacts
├── data/derived/           # db_term_mapping + extract summaries
├── tools/                  # export, stats, extractors, harvest
├── workflows/db_term_mapping/
└── src/xenosite/xmet/      # Python path helpers
```

## Editing workflow

1. Edit `data/ontology/xmet.yaml` (or run a mapping/fill script).
2. `make ontology-export`
3. Run competency / stats as needed.
4. Commit and push this repo; bump the pin in `xenosite-tagger` if consumers
   should pick up the change.

## License

MIT — see [LICENSE](LICENSE).
