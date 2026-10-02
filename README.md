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
├── src/xenosite/xmet/      # Python path helpers
├── site.config.yaml        # website: all project-specific settings
├── content/                # website: all prose (Markdown pages, check explanations)
├── tools/sitegen/          # website: generic data generator (YAML → JSON contract, RDF, .htaccess)
├── site/                   # website: generic Astro + Tailwind renderer
└── w3id/xenosite/xmet/     # generated .htaccess for perma-id/w3id.org
```

## Editing workflow

1. Edit `data/ontology/xmet.yaml` (or run a mapping/fill script).
2. `make ontology-export`
3. Run competency / stats as needed.
4. Commit and push this repo; bump the pin in `xenosite-tagger` if consumers
   should pick up the change.

## Validating against the XMET spec

`xenosite-xmet` ships the spec checks as a library (`xenosite.xmet.validate`) and
a command, `xmet-validate`. XMET's own tests call the same functions, so a
sibling repository that passes `xmet-validate` meets the spec XMET enforces on
itself.

| Command | Run from | Checks |
| --- | --- | --- |
| `xmet-validate ontology` | anywhere | hierarchy, relations, definitions, SSSOM discipline |
| `xmet-validate forest PATH/rules.rs` | Forest | every live pattern has a chemist home; no SSSOM row for a removed pattern; PhaseOne leaves nest under reaction class |
| `xmet-validate tagger PATH/rules` | tagger | every SMARTS rule has an exactMatch home; no SSSOM row for a removed rule |
| `xmet-validate curies PATH…` | any consumer | every `xmet:` CURIE is live; retired ids name their replacement |
| `xmet-validate all --forest-rules-rs … --tagger-rules-dir … --curies …` | CI | all of the above in one run |

Add `--forest-sssom FILE` / `--tagger-sssom FILE` to check a regenerated
mapping before proposing it to XMET, and `--json` for machine-readable output.
Exit status is 1 when any check fails; findings listed in
`data/mappings/validation-xfail.tsv` are reported as expected failures.

```bash
# from a repo that vendors xenosite-xmet as a submodule
uv run --project xenosite-xmet xmet-validate tagger crates/xenosite-tagger/data/rules
# from any repo, without a checkout (the wheel bundles the ontology and mappings)
uvx --from git+https://github.com/swamidasslab/xenosite-xmet xmet-validate forest src/rules.rs
```

```python
from xenosite.xmet.validate import validate_forest

def test_forest_meets_xmet_spec():
    report = validate_forest("src/rules.rs")
    assert report.ok, report.text()
```

## Proposing and applying edits

Edits arrive as **patches**: small YAML changesets in `data/patches/pending/`,
applied atomically and validated only in their final state (format:
[`data/patches/README.md`](data/patches/README.md)). The site's *Suggest an edit*
form writes them and opens them as pull requests.

The **Patches** workflow comments on each patch PR with what changes and which
spec and quality findings the patch fixes or introduces versus `main`. It runs
only code from `main`; the PR's patch files are read as data. Maintainers reply
`/apply` (optionally `/apply #12 #15` to batch several proposals) to get a PR
that applies them to `xmet.yaml`, regenerates exports, and passes tests, or
`/reject <reason>` to close.

Locally: `uv run python tools/patch_review.py PATCH…` (full review),
`uv run xmet-edit check|apply|list`. Applying rewrites only the concepts and
fields a patch changes, mints ids after the last one used, and forwards remap
rows when a concept is retired.

## Website

A static browser for the vocabulary — tree, per-concept pages, search, and
automated quality notes — is built from `xmet.yaml` and deployed to GitHub Pages
at <https://swamidasslab.github.io/xenosite-xmet/>. Concept IRIs
(`https://w3id.org/xenosite/xmet/{id}`) resolve to its pages through w3id.org.

```bash
make site-serve   # live preview at http://localhost:4321/xenosite-xmet/
make site         # full build (incl. search index) into site/dist
```

The site code is generic: nothing in `site/` or `tools/sitegen/` names this
project (a test enforces it). To change what the site says or shows:

| To change… | Edit |
| --- | --- |
| Titles, URLs, theme colour, relations shown, quality thresholds, downloads | `site.config.yaml` |
| Home, About, Contribute, and other page text | `content/pages/*.md` (frontmatter `nav_order` adds a page to the menu) |
| Explanation of a quality check | `content/checks/<check>.md` |
| A concept's label, definition, synonyms, links | `data/ontology/xmet.yaml` |
| Longer notes or examples for one concept | `data/ontology/terms/<id>.md` (see the README there) |

In Markdown, `[[4000009]]` links a concept by its current label,
`{{stats.concepts}}` inserts a live count, and relative links (`browse/`) resolve
against the site base.

The **Site** workflow runs only on `main`: it runs the full test suite and builds
the site, and deploys to Pages only if both pass. Regenerated
`w3id/xenosite/xmet/.htaccess` must be committed (CI checks it is current) and
submitted to [perma-id/w3id.org](https://github.com/perma-id/w3id.org) when it
changes.

## License

MIT — see [LICENSE](LICENSE).
