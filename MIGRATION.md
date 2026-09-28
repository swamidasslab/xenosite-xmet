# Migration notes (temporary)

Internal consumers: XMET live CURIEs were renumbered to a dense opaque block
`xmet:4000000`…`xmet:4000405` (no hierarchy in the number). This file is a short
pointer until tagger emits and downstream pins catch up; delete when obsolete.

## ID remap (old → new)

| File | Role |
| --- | --- |
| [`data/mappings/xmet-id-renumber.tsv`](data/mappings/xmet-id-renumber.tsv) | **Full cut:** every live pre-renumber id → new id (+ label) |
| [`data/mappings/xmet-id-remap.tsv`](data/mappings/xmet-id-remap.tsv) | Ongoing ledger: merges, retires, moves, and `renumbered` rows from the cut |

Resolve a stale CURIE: look it up in `xmet-id-renumber.tsv` first; if absent,
follow `xmet-id-remap.tsv` (`old_id` → `new_id`) until you hit a live id (or a
retired row with empty `new_id`).

Replay / docs only: `uv run python tools/renumber_xmet_ids.py` (already applied;
`--dry-run` available). Next free mint: `xmet:4000406`.

## Forest and tagger mappings

Subject column is already on **new** XMET ids.

| File | Maps |
| --- | --- |
| [`data/mappings/xmet-forest.sssom.tsv`](data/mappings/xmet-forest.sssom.tsv) | XMET ↔ Metabolic Forest (`forest.ruleset:` / `forest.rule:` / `forest.pattern:`). Optional `always_with` descriptors. |
| [`data/mappings/xmet-tagger.sssom.tsv`](data/mappings/xmet-tagger.sssom.tsv) | XMET ↔ tagger SMARTS rules (`rule:…`). Refresh: `make rebuild-tagger-sssom` from a tagger checkout. |

Other SSSOM in the same directory (mesh / mop / udm / external) likewise use
post-renumber subjects. Convenience views: `data/mappings/views/`.

## Caveat for tagger

Ontology + SSSOM here are on `4000000+`. Tagger rule **emit** lists on `main`
may still cite pre-redesign CURIEs — treat `xmet-tagger.sssom.tsv` as the
bridge until emits are rewritten and the submodule pin is bumped.
