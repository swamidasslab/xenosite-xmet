# Related ontologies and XMET positioning

## Positioning

XMET is a **med-chem-oriented SKOS thesaurus** for xenobiotic metabolism reaction
naming, site-localized reaction labels, structural transformation tags,
product/liability classes, and mappings to existing biochemical and chemical
ontologies.

It fills a real gap: **not** an enzyme ontology, pathway ontology, compound
ontology, or named-synthesis ontology. It is the missing layer between
reaction-generating SMARTS/rules and human-useful med-chem metabolism names.

**RXNO + MOP** are the closest actual reaction ontologies, but they are
synthesis / name-reaction oriented, not xenobiotic-metabolism oriented. XMET
stays **separate and SKOS-first**, with explicit SSSOM mappings to
RXNO / MOP / GO / ChEBI / Rhea / KEGG / MeSH / UDM (and ECO / CHMO for evidence),
rather than extending any one of them. Do **not** grow a full chemical
ontology here — metabolism-specific terms only ([`SCOPE.md`](SCOPE.md)).

## Closest resources (ordered)

| Resource | Why it matters | Fit |
| --- | --- | --- |
| **MOP** (Molecular Process Ontology) | Generic molecular processes (cyclization, methylation, epoxidation, …). Best chemical-process grounding for exactMatch when defs align. | High chemistry fit |
| **UDM** (Pistoia Alliance Unified Data Model) | Open reactionClass vocabulary grounded in MOP/RXNO ([`udm_6_0_0_reaction_classes.xsd`](https://github.com/PistoiaAlliance/UDM/blob/master/udm_6_0_0_reaction_classes.xsd)). Use enum **labels** + mop.obo defs; do **not** trust XSD XML comments for IDs (known mismatches). | High for exact process leaves |
| **RXNO** (Name Reaction Ontology) | Named organic / synthesis reactions. Useful architecture; low xenobiotic domain fit. Verify every CURIE at source before mapping. | High structural fit, low domain fit |
| **GO** xenobiotic metabolic process (`GO:0006805`) | Best existing biological anchor for xenobiotic metabolism (includes synonyms like drug metabolism). Process biology, not reaction naming. | High domain fit, low reaction-detail fit |
| **ChEBI** | Essential for product classes, conjugate groups, chemical roles, and small-molecule grounding. | Essential companion |
| **Rhea** | Best curated biochemical reaction knowledgebase; ChEBI participants; UniProtKB enzyme/transporter annotation. | Strong reaction grounding, not med-chem naming |
| **KEGG REACTION / RCLASS / Reaction Modules** | RCLASS / modules are based on chemical structure transformation patterns rather than enzyme identity. Soft crosswalks only unless identity is proven. | High operational relevance |
| **MeSH** | Literature indexing and synonyms. Too coarse for structural reaction tagging alone. | Literature/search fit |
| **ECO** (Evidence & Conclusion Ontology) | Evidence provenance. | Evidence spine |
| **CHMO** (Chemical Methods Ontology) | Assay/instrument/method evidence. | Evidence/method spine |
| **PROV-O / Dublin Core / SIO-like patterns** | Provenance, versioning, assertions, sources, generated-by. | Infrastructure |

## Mapping policy

| Predicate | Use |
| --- | --- |
| `skos:exactMatch` | **True identity only.** Require: (1) preferred labels match, (2) definitions assert the same chemistry, (3) object CURIE verified in the source ontology (OLS/OBO), not from inherited SSSOM text. If uncertain, **omit**. For Forest: chemist home ↔ `forest.rule` / `forest.pattern` when intentionally identical. |
| `skos:closeMatch` | Strong near-identity (Forest rules/patterns: near-identity sibling when a better exactMatch exists, e.g. EpoxideHydration under epoxide opening). |
| `skos:broadMatch` / `skos:narrowMatch` | Coarser/finer — do not expand this pass |
| `skos:relatedMatch` | **Forest rulesets only** (`forest.ruleset:…`). No YAML `related_match`; no relatedMatch on external/MeSH/MOP/tagger/rule/pattern rows unless explicitly re-approved. |
| `xmet:relatedTo` | Soft cross-spine association in YAML (`related_to:`); not SSSOM / not hierarchy (e.g. multistep ↔ composite). |

Checked-in SSSOM:

| File | Targets |
| --- | --- |
| [`../mappings/xmet-udm.sssom.tsv`](../mappings/xmet-udm.sssom.tsv) | High-confidence exactMatch via UDM enums → MOP |
| [`../mappings/xmet-mop.sssom.tsv`](../mappings/xmet-mop.sssom.tsv) | MOP exactMatch (soft relatedMatch removed) |
| [`../mappings/xmet-mesh.sssom.tsv`](../mappings/xmet-mesh.sssom.tsv) | MeSH close/broad only (relatedMatch removed) |
| [`../mappings/xmet-forest.sssom.tsv`](../mappings/xmet-forest.sssom.tsv) | Opaque Metabolic Forest CURIEs |
| [`../mappings/xmet-tagger.sssom.tsv`](../mappings/xmet-tagger.sssom.tsv) | Opaque xenosite-tagger `rule:…` SMARTS rules |
| [`../mappings/xmet-external.sssom.tsv`](../mappings/xmet-external.sssom.tsv) | GO close/broad anchors (ChEBI/Rhea/KEGG relatedMatch removed) |
| [`../mappings/validation-xfail.tsv`](../mappings/validation-xfail.tsv) | Approved validator xfails |

Harvest tooling may pull candidates; only promote rows that meet the exactMatch bar
above. Never invent parallel hierarchies.

## Forest colors vs chemical ancestry

Chemical `skos:broader` must be a true subtype. Forest ruleset membership is separate:

| Ruleset | Role |
| --- | --- |
| SO, UO, DH, HD, RD | Rainbow **five colors** (operational Phase I categories) |
| CJ | Conjugation fork (transfer vs adduct) — auxiliary to the five colors |
| PhaseOne | Disposition-side Phase I catalog association |

A rule may be listed under a Forest color without that color being its chemical parent (e.g. Dehydration under isoredox chemically; RD membership remains operational via SSSOM / catalog).

Representation variants (OH vs OH/O−, mapped vs unmapped, charge encoding) are **not** separate chemical concepts. Multiple Forest patterns or tagger rules may `exactMatch` the same chemist home; each pattern/rule still has exactly one home.
