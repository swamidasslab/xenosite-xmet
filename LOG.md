# Lab log

## 2026-09-27

- Prodrug pipeline alignment: SSSOM `xmet:2300012` ↔ `CHEBI:50266`; synonyms
  for prodrug / active metabolite / CES family; isoform leaves CES1/CES2,
  CYP3A4/CYP3A5 (`xmet:2100232`–`2100235`). Export: 947 concepts.
- Extracted from `xenosite-tagger` via `git filter-repo` (ontology, mappings,
  competency, db_term_mapping, ontology tools) with path history preserved.
- Concept CURIE prefix is `xmet:` (renamed from `xrm:` in tagger tip before extract).
- No RuleSet YAML / rule-bridge here — owned by xenosite-tagger.
