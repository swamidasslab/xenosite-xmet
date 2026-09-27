# metxbiodb reaction terms → XRM mapping analysis

**Ontology fills applied for approved categories** (reactive-metabolite binding,
cyanide, antonym inverses, high-count facet gaps). Further mid-fuzzy adjudication still open.

This report covers **one dataset only** (not merged with the other).

## Summary

- Dataset: **`metxbiodb`**
- Source terms scored: **284**
- Strong-confidence matches: **98** terms (1161 occurrences; 55.0% of labeled occurrences).
- Residual (not strong): **186** terms (949 occurrences).
- Term coverage (strong/all): **34.5%**

### First-pass confidence bins (pre-adjudication)

| Confidence | Terms | Occurrences |
| --- | ---: | ---: |
| `alias` | 29 | 952 |
| `antonym_of` | 1 | 1 |
| `compositional` | 160 | 899 |
| `exact_pref` | 21 | 79 |
| `exact_synonym` | 6 | 16 |
| `fuzzy_high` | 12 | 17 |
| `fuzzy_mid` | 28 | 91 |
| `unmatched` | 27 | 55 |

## Residual gap buckets

Terms that did **not** land in the high-quality strong-match list.

| Bucket | Terms | Occurrences | Meaning |
| --- | ---: | ---: | --- |
| `site_compositional` | 129 | 816 | Qualified phrases; head already in XRM — use bundles/templates |
| `existing_facet_gap` | 43 | 97 | Likely missing leaf/synonym under an existing reaction facet |
| `coverage_decision_unknown` | 8 | 16 | Needs a human cover/exclude decision |
| `needs_adjudication` | 3 | 16 | Algorithm match present; decision still open |
| `coverage_decision_exclude` | 3 | 4 | Propose exclude from reaction-type spine |

### `site_compositional`

Qualified phrases; head already in XRM — use bundles/templates

| Term | Count | Notes |
| --- | ---: | --- |
| Aromatic -OH glucuronidation | 99 | o-glucuronidation |
| Aromatic hydroxylation of fused benzene ring | 68 | aromatic hydroxylation |
| Hydroxylation of alicyclic secondary carbon | 46 | hydroxylation |
| N-dealkylation of alicyclic tertiary amine | 34 | n-dealkylation |
| N-dealkylation of acyclic tertiary amine | 26 | n-dealkylation |
| N-dealkylation of acyclic secondary amine | 25 | n-dealkylation |
| Aliphatic hydroxylation of methyl carbon adjacent to aromatic ring | 25 | aliphatic hydroxylation |
| p-Hydroxylation of monosubstituted benzene | 24 | para-hydroxylation |
| Hydroxylation of terminal methyl | 21 | hydroxylation |
| Alkyl-OH glucuronidation | 19 | o-glucuronidation |
| O-glucuronidation of aliphatic acid | 17 | o-glucuronidation |
| Hydroxylation of aromatic carbon ortho to halide group | 14 | hydroxylation |

### `existing_facet_gap`

Likely missing leaf/synonym under an existing reaction facet

| Term | Count | Notes |
| --- | ---: | --- |
| O-aryl dealkylation not adjacent to substituted carbon | 19 | o-aryl dealkylation |
| O-aryl dealkylation adjacent to substituted carbon | 10 | o-aryl dealkylation |
| 4-OH sulfonation of phenolic compound | 7 | 4-oh sulfonation |
| GSH-conjugation of organohalide | 7 | gsh-conjugation |
| 3-Hydroxylation of 5-aryl-1,4-benzodiazepine | 4 | 3-hydroxylation |
| 3-OH sulfonation of phenolic compound | 4 | 3-oh sulfonation |
| N-dealkoxylation of N-aryl-N-chloroacetamide | 3 | n-dealkoxylation |
| N-demethoxymethylation | 3 | N-demethylation |
| 2-Hydroxylation of 1,4-disubstituted benzene | 2 | 2-hydroxylation |
| 7-Hydroxylation of coumarin | 2 | 7-hydroxylation |
| 4-alkyl hydroxylation of oxoazaphosphorine | 2 | 4-alkyl hydroxylation |
| 4'-Deydroxylation of substitued benzene | 2 | 4 -dehydroxylation |

### `coverage_decision_unknown`

Needs a human cover/exclude decision

| Term | Count | Notes |
| --- | ---: | --- |
| Terminal desaturation | 5 | best below mid threshold |
| Methylenedioxy ring opening | 2 | best below mid threshold |
| 2,4-thiazolidinedione ring opening | 2 | best below mid threshold |
| Flavan-3-ol C-ring fission | 2 | best below mid threshold |
| Anthocyanidin C-ring fission | 2 | best below mid threshold |
| Deamino | 1 | best below mid threshold |
| NS-cleavage | 1 | best below mid threshold |
| Isoflavanone C-ring fission | 1 | best below mid threshold |

### `needs_adjudication`

Algorithm match present; decision still open

| Term | Count | Notes |
| --- | ---: | --- |
| Alpha hydroxylation of carbonyl group | 14 | alpha hydroxylation |
| N-hydroxy glucuronidation | 1 | carbamoyl glucuronidation |
| Aromatic O-glucuronidation | 1 | alcoholic glucuronidation |

### `coverage_decision_exclude`

Propose exclude from reaction-type spine

| Term | Count | Notes |
| --- | ---: | --- |
| Unknown reaction | 2 | best below mid threshold |
| Nifedipine Oxidation | 1 | best below mid threshold |
| Unknown Reduction | 1 | best below mid threshold |

## Recommended next actions (not yet executed)

1. **Accept** `data/derived/db_term_mapping/metxbiodb/strong_matches.tsv` as the crosswalk seed for this dataset.
2. **Site compositional**: do not mint combinatorial concepts; use site_type + templates.
3. **Existing facet gaps**: review high-count leaves for synonym adds vs new concepts.
4. **Broad classes**: map umbrellas as `broadMatch` to parents; child inventory separately.
5. **Coverage excludes**: confirm binding / optical / non-metabolic stay off reaction-type spine.

Artifacts (this dataset):

- `data/derived/db_term_mapping/metxbiodb/matches_scored.tsv`
- `data/derived/db_term_mapping/metxbiodb/strong_matches.tsv`
- `data/derived/db_term_mapping/metxbiodb/residual_terms.tsv`
- `data/derived/db_term_mapping/metxbiodb/gap_analysis.tsv`
- `workflows/db_term_mapping/resources/adjudications_metxbiodb.tsv`

