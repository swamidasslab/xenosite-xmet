# xenosite-xmet

XMET — xenobiotic metabolism SKOS thesaurus and ontology tooling for [xenosite](https://xenosite.org).

This repository holds the **authoring source** (`data/ontology/xmet.yaml`), exported SKOS,
SSSOM mappings, competency tests, and the MetXBioDB/AMD term-mapping workflow.

The reaction **tagger / RuleSet engine** lives in
[`swamidasslab/xenosite-tagger`](https://github.com/swamidasslab/xenosite-tagger), which
consumes this repo as a git submodule. XMET does not own RuleSet YAML or rule-bridge scripts;
tagger may refresh SSSOM mappings here later.

## Layout

- `data/ontology/` — `xmet.yaml` (source) + `xmet.skos.jsonld` / TTL / SHACL
- `data/mappings/` — SSSOM TSV snapshot (+ views)
- `data/competency/` — competency questions and fixtures
- `tools/` — YAML→SKOS export, ontology stats, extractors, harvest
- `workflows/db_term_mapping/` — term → XMET mapping Snakemake workflow

## Setup

```bash
uv sync
make ontology-export
make ontology-stats
```

## Clone note (as tagger submodule)

```bash
git clone --recurse-submodules git@github.com:swamidasslab/xenosite-tagger.git
```

Concept CURIEs use the `xmet:` prefix (e.g. `xmet:1100000`).
