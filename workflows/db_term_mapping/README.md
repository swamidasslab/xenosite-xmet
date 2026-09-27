# DB reaction-term → XRM mapping (per dataset)

MetXBioDB and AMD are **never combined**. Each dataset has its own
`data/derived/db_term_mapping/<dataset>/` tree (committed). Raw DBs stay local
under `data/` and are gitignored.

## Run

From repo root (requires prior extract outputs under `data/derived/db_extracts/`):

```bash
make db-term-mapping
# equivalent:
uv run snakemake -s workflows/db_term_mapping/Snakefile -c1
uv run snakemake -s workflows/db_term_mapping/Snakefile -c1 metxbiodb
uv run snakemake -s workflows/db_term_mapping/Snakefile -c1 amd
```

## Pipeline (each dataset)

1. `prepare_terms` — inventory from that dataset's counts TSV
2. `match_terms` — confidence bins vs XRM label index (+ shared `aliases.tsv`)
3. `prepare_review` — uncertain / high-count unmatched queue
4. `apply_adjudications` — merge `resources/adjudications_<dataset>.tsv` → strong + residual
5. `analyze_gaps` — residual gap buckets + markdown report

Shared: `ontology_index.tsv` built once from `xrm.yaml`.

## Adjudication decisions

In `adjudications_<dataset>.tsv`:

| decision | Effect |
| --- | --- |
| `accept` | Promote proposed match to strong |
| `accept_as` | Strong, using `adj_xrm_id` / `adj_preferred_label` |
| `synonym_of` | Same as `accept_as` (synonym gap) |
| `reject` / `no_match` | Force residual unmatched |
| `out_of_scope` | Residual; gap bucket exclude |
| `compositional_only` | Residual; treat as site-qualified, not identity match |

Auto-strong without adjudication: `exact_pref`, `exact_synonym`, `alias`, `fuzzy_high`.
