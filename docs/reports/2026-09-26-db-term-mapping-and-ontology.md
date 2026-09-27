# Report: DB term mapping and ontology fills (2026-09-26)

## What we did

Built a **per-dataset** Snakemake workflow (`workflows/db_term_mapping/`) that maps
MetXBioDB Reaction Type and AMD RXNCLASS labels to XRM separately (never merged),
with confidence bins, adjudication TSV, strong matches, and gap analysis.

Extractors write countable inventories and capped validation examples under
`data/derived/db_extracts/{metxbiodb,amd}/` (committed). Raw MetXBioDB JSON and
AMD parquet stay local and are not committed. Full per-row `examples.tsv` is
optional (`--write-examples`) and kept under gitignored `artifacts/`.

Mapping outputs live under `data/derived/db_term_mapping/`.

## Mapping outcomes (after adjudication + ontology fills)

| Dataset | Strong terms | Occurrence coverage (approx.) |
| --- | ---: | ---: |
| MetXBioDB | ~98 | ~55% |
| AMD | ~170 | ~95% |

MetX residual volume is mostly **site-compositional** phrases already expressible
as transformation + site bundles (~145/161 refined as composite-covered). AMD
coverage is high on coarse umbrellas; mid-fuzzy adjudication queue remains open.

## Ontology fills (approved directions)

- **Reactive metabolite:** DNA / protein / covalent / related macromolecule binding;
  cyanidation / decyanidation.
- **Facet gaps + antonyms:** alkylation family, deconjugation inverses
  (deglucuronidation, desulfation, …), decarboxylation, esterification,
  cyclization, etc., with `related_match` antonym wiring; negation-prefix detector
  in the workflow.
- **Structural alerts** under medchem liability: furan, thiophene, triple bond
  (alkyne); plus `alkyne site`.
- **Experimental context** under biological context: in vivo / in vitro settings;
  assay systems (hepatocytes, microsomes, baculosomes, S9, …); AMD-basic species
  adds; reparented tissue/species/matrix leaves. Starter
  `xrm-reaction-context-expectations.tsv` with child inheritance + exclusions
  (`likely_in` / `observed_in` / `unlikely_in`).
- MetX **Thiohene → Thiophene** normalization in extracts + ontology altLabels.

## Tooling

- `make ontology-stats` — terminal spine/label/mapping inventory (bands = floor, not cap).
- `make ontology-export` — regenerate SKOS from YAML.

## Planned (not done)

- Rearrangement hierarchy: tautomerization / isomerization / epimerization under a
  broad rearrangement parent.
- Expand structural-alert seeds and reaction↔context expectation rows.
- Finish AMD mid-fuzzy review queue.

## How to re-run

```bash
uv run python crates/xenosite-tagger/tools/extract_metxbiodb.py
uv run python crates/xenosite-tagger/tools/extract_amd.py
uv run snakemake -s workflows/db_term_mapping/Snakefile -c1
make ontology-stats
```
