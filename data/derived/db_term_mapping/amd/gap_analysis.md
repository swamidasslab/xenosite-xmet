# amd reaction terms → XRM mapping analysis

**Ontology fills applied for approved categories** (reactive-metabolite binding,
cyanide, antonym inverses, high-count facet gaps). Further mid-fuzzy adjudication still open.

This report covers **one dataset only** (not merged with the other).

## Summary

- Dataset: **`amd`**
- Source terms scored: **297**
- Strong-confidence matches: **170** terms (157592 occurrences; 95.0% of labeled occurrences).
- Residual (not strong): **127** terms (8319 occurrences).
- Term coverage (strong/all): **57.2%**

### First-pass confidence bins (pre-adjudication)

| Confidence | Terms | Occurrences |
| --- | ---: | ---: |
| `alias` | 19 | 96226 |
| `antonym_of` | 2 | 594 |
| `exact_pref` | 86 | 47895 |
| `exact_synonym` | 32 | 4844 |
| `fuzzy_high` | 23 | 1269 |
| `fuzzy_mid` | 99 | 10271 |
| `unmatched` | 36 | 4812 |

## Residual gap buckets

Terms that did **not** land in the high-quality strong-match list.

| Bucket | Terms | Occurrences | Meaning |
| --- | ---: | ---: | --- |
| `needs_adjudication` | 73 | 1238 | Algorithm match present; decision still open |
| `coverage_decision_unknown` | 38 | 3587 | Needs a human cover/exclude decision |
| `existing_facet_gap` | 7 | 66 | Likely missing leaf/synonym under an existing reaction facet |
| `coverage_decision_exclude` | 5 | 2401 | Propose exclude from reaction-type spine |
| `site_compositional` | 2 | 967 | Qualified phrases; head already in XRM — use bundles/templates |
| `broad_class` | 2 | 60 | Coarse umbrella needing systematic child mapping |

### `needs_adjudication`

Algorithm match present; decision still open

| Term | Count | Notes |
| --- | ---: | --- |
| Peroxidation | 78 | epoxidation |
| S-Deacylation | 78 | deacylation |
| Methiolation | 77 | methylation |
| Denitration | 69 | denitrosation |
| C-Deacylation | 57 | deacylation |
| Methoxylation | 48 | methylation |
| Oxygenation | 45 | dioxygenation |
| C-Methylation | 39 | N-methylation |
| P-Oxidation | 39 | epoxidation |
| C-Deamination | 36 | deamination |
| Transconjugation | 35 | conjugation |
| S-Dearylation | 35 | dearylation |

### `coverage_decision_unknown`

Needs a human cover/exclude decision

| Term | Count | Notes |
| --- | ---: | --- |
| Chain Shortening | 923 | best below mid threshold |
| Cleavage | 577 | azo cleavage |
| Elimination | 540 | deamination |
| Deamidation | 244 | deamination |
| Amidation | 195 | amination |
| Chain Elongation | 185 | best below mid threshold |
| Quaternization | 156 | best below mid threshold |
| Dehydrohalogenation | 115 | dehydrogenation |
| Aromatic Methoxylation | 104 | dehydroxylation |
| Thiolation | 93 | sulfuration |
| C-Methoxylation | 79 | N-methylation |
| Polyglutamation | 61 | best below mid threshold |

### `existing_facet_gap`

Likely missing leaf/synonym under an existing reaction facet

| Term | Count | Notes |
| --- | ---: | --- |
| Oxidative Cleavage | 20 | best below mid threshold |
| Aromatic Sulfonation | 15 | best below mid threshold |
| Allylic Oxidation | 8 | best below mid threshold |
| Aliphatic Peroxidation | 8 | aliphatic epoxidation |
| Oxidative Deboronation | 8 | oxidative debromination |
| Reductive Amination | 6 | best below mid threshold |
| Transformylation | 1 | chemical transformation |

### `coverage_decision_exclude`

Propose exclude from reaction-type spine

| Term | Count | Notes |
| --- | ---: | --- |
| Optical Resolution | 1577 | best below mid threshold |
| Condensation | 293 | best below mid threshold |
| Dimerization | 244 | isomerization |
| Inversion | 232 | best below mid threshold |
| Decomplexation | 55 | best below mid threshold |

### `site_compositional`

Qualified phrases; head already in XRM — use bundles/templates

| Term | Count | Notes |
| --- | ---: | --- |
| Nucleophilic Addition | 544 | best below mid threshold |
| Nucleophilic Substitution | 423 | nucleophilic aromatic substitution |

### `broad_class`

Coarse umbrella needing systematic child mapping

| Term | Count | Notes |
| --- | ---: | --- |
| N-Conjugation | 55 | conjugation |
| S-Conjugation | 5 | conjugation |

## Recommended next actions (not yet executed)

1. **Accept** `data/derived/db_term_mapping/amd/strong_matches.tsv` as the crosswalk seed for this dataset.
2. **Site compositional**: do not mint combinatorial concepts; use site_type + templates.
3. **Existing facet gaps**: review high-count leaves for synonym adds vs new concepts.
4. **Broad classes**: map umbrellas as `broadMatch` to parents; child inventory separately.
5. **Coverage excludes**: confirm binding / optical / non-metabolic stay off reaction-type spine.

Artifacts (this dataset):

- `data/derived/db_term_mapping/amd/matches_scored.tsv`
- `data/derived/db_term_mapping/amd/strong_matches.tsv`
- `data/derived/db_term_mapping/amd/residual_terms.tsv`
- `data/derived/db_term_mapping/amd/gap_analysis.tsv`
- `workflows/db_term_mapping/resources/adjudications_amd.tsv`

