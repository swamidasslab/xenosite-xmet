# Annotation bundles and link types

SKOS concepts **name** things. Reaction annotations **combine** them.
Do not mint combinatorial concepts such as
`benzylic_phase_1_hydroxylation_clearance_liability`.

Site-localized display names (`C4 aromatic hydroxylation`, `benzylic hydroxylation @1`)
are generated from templates + `SiteRef` into
[`AnnotationBundle::site_label`](../../src/bundle.rs), not stored as ontology terms.

```rust
let bundles = namer.annotate_smiles("CC", "CCO", &[])?;
// bundles[i].transformation / phase / site_environment / medchem_interpretation / site_label
```

## Identifier policy

IDs are **opaque** CURIEs — do **not** encode spine or chemistry in the number.
Hierarchy lives in `parents:` / `skos:broader` only.

Live inventory was renumbered densely to ``xmet:4000000``…``xmet:4000405``
(see [`../mappings/xmet-id-renumber.tsv`](../mappings/xmet-id-renumber.tsv)).
New mints continue sequentially from ``xmet:4000410`` (``4000406``–``4000409``
used for conjugated-system / quinoid endpoint restructure). Never recycle a
retired CURIE. Merges/retirements/renumbers:
[`../mappings/xmet-id-remap.tsv`](../mappings/xmet-id-remap.tsv).

```bash
uv run python tools/renumber_xmet_ids.py   # already applied; kept for replay docs
```

## Inventory guidance (v0.1)

A useful first band is **~350–500** chemist-facing canonical concepts with
**1,000–2,000** labels/synonyms/mappings — enough to be useful, still curatable.
That band is a **floor for usefulness**, not a hard cap. Extra terms are welcome
when they are well motivated and clear. Prefer clear leaves over combinatorial
compounds. Forest-map rules/patterns are an alias spine counted separately.

### Category bands (primary-spine counting)

Count a concept toward the spine of its **nearest spine-root ancestor** (not the
full polyhierarchy descendant closure — that double-counts leaves under both
chemical transformation and phase I family).

| Spine | Target | Notes |
| --- | --- | --- |
| Phase / pathway role | 10–20 | phase I/II, sequential metabolism, intermediate formation |
| Chemical transformation | 90–140 | Largest core |
| Phase I detailed classes | 25–40 | Rainbow-compatible + finer types |
| Phase II conjugation classes | 40–70 | By attachment atom where useful |
| Product / metabolite class | 70–110 | Quinone, epoxide, GSH adduct, … |
| Site environment | 60–100 | Benzylic, phenol, tertiary amine, heteroarene, … |
| Structural delta | 35–60 | +O, −2H, aromaticity loss, conjugate mass shift |
| Med-chem interpretation | 40–70 | Soft spot, **structural alert** (furan/thiophene/alkyne seeds), bioactivation, blocking, … |
| Evidence / assertion | 30–50 | MS, NMR, predicted/observed/curated/conflict |
| Biological context | 40–100 | Enzyme/tissue/species/matrix/**experimental setting & assay system** (orthogonal) |
| Rule/model provenance | 20–40 | SMARTS, Rainbow class, XenoNet, legacy model |
| Localization templates | — | Not SKOS; see [`site_templates.yml`](site_templates.yml) |
| Leaving group | 20–40 | Departing methyl/ethyl/halide/carboxylate/… fragments |
| Pharmacological role | 10–25 | Active/inactive metabolite, prodrug (metabolism-specific) |
| Annotation about | 5–15 | about parent / product / reaction (not combinatorial) |

## SKOS link types

| Link | Use |
| --- | --- |
| `skos:broader` / `skos:narrower` | Within a spine. **Single parent only** — no multi-inheritance. Cross-axis links use `related_to` / `antonyms`, not a second broader. Representation/encoding variants share one chemical home (multiple SSSOM objects → one subject OK; each object still has one home). |

| `skos:related` / `skos:relatedMatch` | **Not used in YAML.** SSSOM: Forest rulesets only |
| `xmet:relatedTo` (`related_to:` in YAML) | Soft association across spines (e.g. multistep ↔ composite); not hierarchy |
| `xmet:suggests` (`suggests:` in YAML) | Often co-applies (weaker than alwaysWith); e.g. halide leaving group → dehalogenation. List **family roots only** — do not also list `skos:narrower` descendants of a listed target (parent covers children). |
| `xmet:alwaysWith` (`always_with:` in YAML) | Stronger suggests: whenever source applies, target (or a child of a category root) also applies; e.g. dehalogenation → halide leaving group. Nested under suggests in the relation vocab. Same no-redundant-descendant rule when listing multiple targets. |
| `xmet:antonymOf` (`antonyms:` in YAML) | Opposite / inverse transformation pair (symmetric) |
| `skos:exactMatch` | True identity to an external concept (rare) |
| `skos:closeMatch` | Similar MeSH/KEGG/Rhea/model term |
| `skos:broadMatch` / `skos:narrowMatch` | Legacy/model terms broader/narrower than XMET |

## Operational annotation properties (`xmet:`)

These are **assertion / event** links on [`AnnotationBundle`], not thesaurus
identity parents.

| Property | Bundle field |
| --- | --- |
| `xmet:hasPhase` | `phase` |
| `xmet:hasTransformation` | `transformation` |
| `xmet:hasProductClass` | `product_class` |
| `xmet:hasSiteEnvironment` | `site_environment` |
| `xmet:hasStructuralDelta` | `structural_delta` |
| `xmet:hasMedChemInterpretation` | `medchem_interpretation` |
| `xmet:hasEvidenceType` | `evidence_type` |
| `xmet:hasBiologicalContext` | `biological_context` |
| `xmet:likelyInContext` | Reaction class (and optional children) expected to proceed in an experimental setting / assay / matrix / species |
| `xmet:observedInContext` | Metabolites of this class reported/found in that context (e.g. urine, plasma) |
| `xmet:unlikelyInContext` | Class generally not expected in that system (e.g. sulfation in classical microsomes) |
| `xmet:generatedByRule` | `generated_by_rule` |
| `xmet:mapsModelOutput` | (via SSSOM / provenance leaves) |
| `xmet:localizesToSite` | `site` + `site_label` |
| `xmet:mayPrecede` / `xmet:mayFollow` | SKOS `relatedMatch` pathway pairs |
| `xmet:bioactivatesTo` / `xmet:detoxifiesTo` | medchem ↔ product_class related pairs |
| `xmet:hasConjugateGroup` | phase2 / product_class conjugates |
| `xmet:hasAttachmentAtomType` | site environment attachment-atom leaves |
| `xmet:hasLeavingGroup` | `leaving_group` |
| `xmet:hasPharmacologicalRole` | `pharmacological_role` |
| `xmet:aboutParent` / `aboutProduct` / `aboutReaction` | distinguish tag target |

### Reaction class ↔ experimental context

Curated priors (not hard OWL axioms) live in
[`../mappings/xmet-reaction-context-expectations.tsv`](../mappings/xmet-reaction-context-expectations.tsv):

| Column | Meaning |
| --- | --- |
| `reaction_id` | XMET reaction / transformation concept |
| `context_id` | Biological-context leaf (assay, matrix, species, setting) |
| `relation` | `likely_in` / `observed_in` / `unlikely_in` (→ `xmet:likelyInContext` etc.) |
| `inherit_children` | If true, apply to `skos:narrower` descendants |
| `exclude_reaction_ids` | Pipe-separated child CURIEs to skip when inheriting |

Combinations stay out of the SKOS inventory; bundles attach context via
`xmet:hasBiologicalContext` and these expectation predicates.

## Bundle shape

```json
{
  "transformation": "xmet:4000018",
  "phase": "xmet:4000001",
  "site_environment": ["xmet:1600014"],
  "structural_delta": ["xmet:1700012"],
  "medchem_interpretation": ["xmet:1400010"],
  "site_label": "benzylic hydroxylation @1",
  "site": {"map_nums": [1]},
  "xmet_properties": ["xmet:hasPhase", "xmet:hasTransformation", "xmet:localizesToSite"]
}
```
