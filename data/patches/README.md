# Edit patches

A patch proposes one coherent change to the ontology. It is reviewed
automatically when proposed and applied to `../ontology/xmet.yaml` only after a
maintainer accepts it.

- `pending/` — proposals (one YAML file each, added by pull request)
- `applied/` — accepted patches, kept as provenance with the ids they minted

The easiest way to write one is the **Suggest an edit** form on any concept page
of the site. To write one by hand:

```yaml
id: 2026-10-02-split-c-dealkylation        # unique; becomes the file name
author: "@your-github-name"                 # optional
rationale: Why this change is right.        # required for review
changes:                                    # applied in order, all or nothing
  - op: new_concept
    ref: new:tert                           # placeholder; real xmet: id assigned on apply
    label: tertiary C-dealkylation
    definition: C-dealkylation at a tertiary carbon …
    parent: xmet:4000046
    synonyms: [tert C-dealkylation]         # optional
  - op: move
    concept: xmet:4000317
    from: xmet:4000046                      # optional guard: fails if the parent changed
    to: new:tert
  - op: set_definition
    concept: xmet:4000046
    expect: "current definition …"          # optional guard
    value: "new definition …"
```

| op | fields |
| --- | --- |
| `set_label` | `concept`, `value`, optional `expect` |
| `set_definition` | `concept`, `value`, optional `expect` |
| `add_synonym` / `remove_synonym` | `concept`, `value` |
| `move` | `concept`, `to`, optional `from` |
| `add_relation` / `remove_relation` | `concept`, `relation` (`related_to`, `antonyms`, `suggests`, `always_with`, `is_part_of`, `has_part`, …), `target` |
| `new_concept` | `ref` (`new:<name>`), `label`, `definition`, `parent`, optional `synonyms` |
| `retire` | `concept`, `replaced_by`, optional `children_to`, `change_type`, `note` — children and links move to the replacement; the remap table records it |

Check a patch locally — what it changes, and which spec and quality findings it
fixes or introduces compared with the current ontology:

```bash
uv run python tools/patch_review.py data/patches/pending/my-edit.yaml   # spec + quality
uv run xmet-edit check data/patches/pending/my-edit.yaml                # spec only
uv run xmet-edit apply data/patches/pending/my-edit.yaml                # maintainers
```
