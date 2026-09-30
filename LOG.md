# Lab log

## 2026-09-29

- Forest SSSOM sync from metabolite (`xf:` CURIEs). Dropped short-code catalog
  rows (SO/UO/CJ) and redundant Dehydrogenation/Hydrolysis `relatedMatch`.
  Mapped Effect-split patterns to precise homes: `dealkylate_cumulated` →
  `4000330` + isocyanate LG; quaternary_alcohol_n/nitro → `4000336` + ox-state
  (+ nitrite LG); `beta_elimination_acid` → `4000305`; `alkene_cumulene` →
  `4000091`; tautomer patterns stay on `4000186`.
- Minted `4000418` nitrite leaving fragment; `4000419`/`4000420` nitroso/nitro
  oxo-leave under dehydration; `4000421`/`4000422` nitroso/nitro N=O reduction
  under oxygen reduction. SSSOM exactMatch for the four Forest dehyd/OR arms.
- Validator/tools accept living ``xf:`` Forest CURIEs (normalize legacy ``forest.rule``/``pattern``/``ruleset``; expand SO/UO/… to long catalog names). Conjugation catalog nesting optional until SSSOM row exists. ``forest_pattern_coverage`` / tree printer updated for w3id ``xf:`` IRIs.



## 2026-09-29

- Hard-fail ``definition_product_ref``: concept definitions must not mention Forest / Xenosite / Rainbow (or forest./forest-map); cleaned 52 defs to chemical prose; pytest coverage.


## 2026-09-29

- Relation vocab: minted ``operationalizes`` under concept relation with children ``predicts``, ``recognizes``, ``enumerates`` (`4000414`–`4000417`); YAML/TTL export predicates wired.


## 2026-09-28

- Tagger SMARTS ``rule:struct-conjugated-system-remodeling``: same phenol→carbonyl
  SMARTS as quinone-like formation, **without** ``aromaticity_change: dearomatize``;
  SSSOM ``exactMatch`` to conjugated-system remodeling (``xmet:4000406``) alongside
  Forest ``QuinoneFormation``. Quinone-like (``4000059`` / struct-quinone-formation)
  keeps the dearomatize gate. Also SSSOM for ``struct-glutathionation`` /
  ``struct-deglutathionation`` / ``struct-decysteination``.

- Parent crate patch bump ``0.6.1``→``0.6.2`` with soft-link cleanup commit.

- Dropped halide LG → dehalogenation ``suggests`` (wrong direction). Keep
  reaction → LG ``alwaysWith`` only (ox/red/isoredox dehalogenation → halide;
  dechlorination → chloride; …). A halide LG also appears in displacement /
  conjugation paths, so it should not imply dehalogenation.

- Soft-link crosstalk cleanup: mass-shift cues prefer **one general** target —
  deethylation −28 → minted ``deethylation`` (4000413) instead of N-+O-fan-out;
  +16 → hydroxylation (not the broader stable-oxygenation shelf). Demethylation −14 /
  cyanide 27 already general/specific-correct. Geminal / family ox-dehal paths
  keep ``alwaysWith`` halide LG only (not F/Cl/Br/I). Tree printer now lists
  ``alwaysWith`` in the relations dump.

- Halide LG ``suggests`` precision: drop generic isoredox/family targets from
  F/Cl/Br/I. Specific LGs now only point at halogen-matched ox/red leaves.
  Minted missing ``oxidative deiodination`` (4000410), ``reductive
  debromination`` (4000411), ``reductive deiodination`` (4000412) so Br/I
  match Cl/F. Generic halide LG still → ox/red/isoredox dehalogenation.

- Mass-shift descriptors: put nominal Da in preferred labels (GSH pyroglutamate
  NL **129 Da**, GSH **+305**, GlcA **+176**, sulfate **+80**, oxygenation
  **+16**, demethylation **−14**, deethylation **−28**, cyanide **27**). Wired
  ``suggests`` to matching reaction classes (glutathione conjugation,
  glucuronidation, sulfation, hydroxylation, demethylation, N-/O-deethylation,
  cyanide conjugation). Prose-only "suggests" in defs was not enough.

- Quinone hierarchy restructure: minted **conjugated-system remodeling**
  (`xmet:4000406`) as Forest `QuinoneFormation` rule home; **nonaromatic
  conjugated-system remodeling** (`4000407`) shelf for rule–pattern gap;
  kept `4000059` quinone-like as tagger home under the parent. Retired
  product-type shelf `4000363` (children hang under quinone-like). Renamed
  `4000364` → quinone-like endpoint transformations; renamed pattern leaves by
  transformation chemistry (`aromatic CH to quinoid carbonyl`, `oxidative
  dehalogenation to quinoid carbonyl`, `hydroxy/amino ring-end
  dehydrogenation` + phenolic/anilinic children `4000408`/`4000409`);
  `has_part` links for composite end-state edits (OH/ox-dehal + DH). Validator
  green; hydroquinone→BQ still emits `4000059`. Definitions aligned to remodeling
  parent / aromatic quinone-like subset / endpoint has_part chemistry. Retargeted
  ``is_part_of`` for dehydrogenation and aromatic hydroxylation from quinone-like
  up to conjugated-system remodeling (``related_to`` quinone-like kept).
  Parent crate patch bump ``0.6.0``→``0.6.1``.

- Trimmed redundant LG ``suggests`` fan-out: **precision-matched** pairs
  (halide→ox/red/isoredox dehalogenation; fluoride→defluorination; chloride→
  dechlorination; bromide→debromination + red/isoredox fallbacks). Dropped
  mechanism-leaf spam under generic halide. Validator ``soft_target_redundant``
  still forbids listing a target that is under another listed target.

## 2026-09-28

- Tagger emit sync from `xmet-tagger.sssom` (`make sync-tagger-emits`): SMARTS
  rules emit live `4000xxxx` reaction-class homes (+ YAML `always_with`); dropped
  non-live/wiped-spine co-emits; restored chemistry tag bridges from Forest SSSOM;
  removed ambiguity/about/pharmacology tag helpers (spines wiped). Runtime spines
  in tagger retargeted to disposition/RC/descriptor/LG. Checkpoint parent commit
  `cbce71e` before this cut for revert.

## 2026-09-28

- Opaque dense renumber of all 406 live concepts to ``xmet:4000000``…``xmet:4000405`` via ``tools/renumber_xmet_ids.py`` (two-phase placeholders; no hierarchy in IDs). Covered ontology + all mapping SSSOM/views/expectations; ledger in ``xmet-id-renumber.tsv``. Chose ``4000000+`` because ``1000000+`` overlapped live ``1xxxxxx`` IDs. Tagger rule emits on main still use pre-redesign CURIEs — separate sync needed.


## 2026-09-28

- Nested relation vocab ``always with`` under ``suggests``. Wired YAML ``always_with`` → ``xmet:alwaysWith``. Upgraded dehalogenation → halide LG from suggests to alwaysWith (generic→halide root; *de*fluorination/chlorination/bromination→matching leaf); LG→reaction stays suggests.


## 2026-09-28

- Dropped invented ``C–C dealkylation`` shelf (`3001197`→`0000204`): Forest ``cc_*`` homes on **C-dealkylation** (peer of N/O/S under dealkylation); synonyms include oxidative C–C cleavage. Renamed quaternary child; rehomed **dearylation** under dealkylation (heteroatom aryl loss, not C–C).


## 2026-09-28

- Extended dealk alwaysWith policy to general ``Dealkylation/*`` (not only N): collapsed 10 ox-state leaves; O-/S-demethylation and O-deethylation reparented under site shelves; validator covers both Dealkylation and NDealkylation pattern families.


## 2026-09-28

- N-dealkylation ox-state leaves collapsed onto site shelves; Forest patterns share homes with SSSOM ``always_with`` to cleaved-carbon ox-state (+ LG when site-fixed). Validator/tests require always_with present and distinct for shared NDealkylation homes.


## 2026-09-28

- Adopted remaining clear hierarchy advice: hydroxylation axes reparented (aromatic / aliphatic / chain / activated under hydroxylation; allylic→activated); epoxide opening→isoredox (HD operational-only); acyl glucuronidation sibling of O-glucuronidation; collapsed 14 representation-twin leaves onto chemical parents; relaxed pattern/tagger subject-uniqueness (object homes still unique).


## 2026-09-28

- Semantic ancestry cleanup (**no multi-inheritance**): deconjugation sibling of conjugation; dehydration→isoredox; generic dehalogenation→RC with ox/red single-parent under UO/RD; aldehyde oxidation sibling of alcohol oxidation; minted C–C dehydrogenation; disulfide under sulfur oxidation; hydration above carbonyl-cleavage; arene-oxide rearrange→rearrangement; multistep→**step count**; quinone-like under RC (hasPart softened to relatedTo); diols single-parent under diol formation; merged duplicate N-demethylation (`0000205`→`3001200`); validator `single_parent` + Dehydration operational-only ruleset nest exemption.


## 2026-09-28

- Relabeled broad Forest-aligned **quinone** homes to **quinone-like species** (quinoid); minted narrow classical **quinone formation** (`xmet:4000394`) under quinone-like products beside quinone-imine and quinone-methide; ortho/para nest under the narrow quinone term. Forest/tagger SSSOM stay on the broad parent.


## 2026-09-28

- Audited quinone-family wording: XMET “quinone” means **quinone-like / quinoid** (two-site oxidation/dehydrogenation collapsing an aromatic system into a non-aromatic conjugated system). Updated defs for quinone formation/products/transformations, ortho/para/imine/methide, reduction, GSH shelves, and related Forest pattern leaves; synonyms include quinoid / quinone-like species.


## 2026-09-28

- Dropped quinone ``stepwise quinone formation`` shelf; moved one-/two-/three-step to reaction-descriptor **multistep** (`xmet:4000393`), ``related_to`` composite transformation (YAML ``related_to`` → ``xmet:relatedTo``).


## 2026-09-28

- Added Forest nesting invariants: patterns ⊂ rules ⊂ rulesets ⊂ parents (`check_forest_nesting` + pytest). Membership from draft colors + CJ + specialized extras; PhaseOne uncolored leaves must sit under reaction class; ruleset homes must nest under oxidation / isoredox / RC / disposition as appropriate.


## 2026-09-28

- Renamed taxonomic unflatten shelves to chemist phrasing (`of`/`with`/…): e.g. N-dealkylation by carbon class → N-dealkylation of alkyl carbons; N-dealkylation by amine degree → N-dealkylation of secondary and tertiary amines; likewise for leaving-fragment, quinone, adduct, GSH, nitro/azo, hydroxylation, and isoredox shelves.


## 2026-09-28

- Unflattened high-fanout shelves (minted intermediate hierarchy): dealkylation
  (heteroatom vs carbon-class/demethyl/methylene/methine/C–C); N-dealkylation
  (amine degree vs carbon-class); hydrolytic cleavage (ester/amide/ether/nitrile/
  deacyl families); isoredox (addition vs removal); LG heteroatom shelf
  (O/N/S/inorganic); quinone (product/mechanism/step-count); adduct (GSH/cyanide/
  macromolecule/mechanism); transfer conjugation (acyl vs heteroatom);
  GSH (epoxide-aziridine/Michael/displacement/special); nitrogen reduction
  (nitro/azo/other); methyl-methylene hydroxylation (chain/activated/aliphatic).
  Also: EpoxideHydration → composite `alkene to vicinal diol pathway` (hasPart
  epoxidation+opening+hydration); GSH H-count and nitro N–O form leaves for
  unique Forest pattern homes. Validator green.

- Stripped all YAML `related_match` (150 edges) and non-ruleset SSSOM
  `relatedMatch` (external/MeSH/MOP/views). **Kept** only Forest
  `forest.ruleset:*` relatedMatch (explicit policy). Validator enforces
  (`yaml_related_match_forbidden`, `sssom_related_match_forbidden`).

- Antonym pairs marked via YAML `antonyms:` → `xmet:antonymOf` (relation vocab
  `antonym of` xmet:4000342). Fuzzy audit skips antonym pairs. Synonym cleanups:
  aromatic epoxidation ≠ arene oxide; mesylate ≠ sulfonate parent label; cyanide
  vs nitrile kept distinct (cross-syns dropped); ether hydrolysis ≠ ether cleavage
  syn. Reparented dehalogenation → isoredox; alkene epoxidation → epoxidation.
  Removed **ring oxidation** (xmet:1100016).

- Tagger SMARTS subject collisions resolved by **level-down children** (not
  detector-twin ontology fakes): OH vs OH/O− splits under hydroxylation /
  aromatic / aliphatic / alcohol oxidation; site-mapped vs unmapped alkene
  epoxidation; carbon oxidation + dioxygenation under oxidation (umbrella
  `struct-oxidation` stays on parent); tertiary/secondary N-dealkylation.
  Retargeted `emit[0]` in tagger YAMLs + SSSOM. Rebuild unique-home green.
  Forest pattern/rule subject collisions still open (GSH H-count, nitro forms,
  EpoxideHydration composite vs Opening/hydrate).

- Mapped all **101** live Forest catalog patterns (was 34 unmatched). Decisions:
  reuse existing chemist homes where identity is clear; mint 17 leaves otherwise
  (NDealkylation mirrors, GSH thiol/alkene/carbonyl/mesylate, sulfation
  epoxide-methyl-sulfone, nitroaromatic charged/neutral). Validator green:
  `forest_pattern_coverage` + unique-home checks.

- Validator hard-fails on unmatched live Forest patterns and on pattern/tagger
  objects mapped to >1 XMET home.

- QuinoneFormation Forest patterns now under quinone formation: single-to-double,
  carbonyl-O addition, halide replacement, dealkylative; iminium→quinone-imine.
  Tree display: dropped inherited `[under …]` Forest tags (direct SSSOM only).

- Descriptor cleanup: consolidated **aromaticity effect** (dearomatization /
  rearomatization); **mass shift** now sibling of structural delta with only
  high-signal drug-dev cues (GSH +305 / NL129, GlcA, sulfate, cyanide,
  demethylation, deethylation, oxygenation); thinned **structural delta** to
  stereochemical change only (retired ~60 engine topology/formula/pathway
  spray terms). Tool: `tools/thin_descriptor_spines.py`.

- Leaving-group hierarchy: nest under **small alkyl**, **carbonyl fragment**,
  **halide**, **heteroatom/small-molecule**, **sulfonate**; keep **no leaving
  group** and **aryl** at top. Matches redesign descriptor sketch.

- Diol shelf (reaction class, not descriptor): **diol formation** with
  **cis-diol formation** (ex cis-dihydroxylation) and **trans-diol formation**
  beneath it. Cis no longer sits above the generic. Trans linked to epoxide
  hydration; composite dihydrodiol pathway `hasPart` includes trans-diol.

- NIH shift: **not a composite** — single rearrangement step. Merged into
  **arene oxide rearrangement to phenol** (`xmet:4000197`); "NIH shift" kept as
  synonym. Composite arenol-conjugation pathway `hasPart` updated.

- Quinone formation: removed from under dehydrogenation; **composite only**.
  `hasPart` aromatic hydroxylation + dehydrogenation (related, not subtype).

- Composite shelf populated: **quinone formation** also under composite (hasPart
  aromatic hydroxylation); minted **arene oxide–trans-dihydrodiol pathway**
  (arene oxide + epoxide hydration) and **arene oxide–arenol conjugation pathway**
  (arene oxide + NIH shift + phenolic GlcA/sulfate). YAML `has_part`/`is_part_of`
  exported as dct:hasPart/isPartOf. Tree shows `[hasPart: …]`.

- Dropped deferred **aromatic/conjugated impact** shelf (`xmet:8000000`–`8`) and
  empty `aromaticity effect`. Rehomed chemist terms: thiophene epoxidation→
  epoxidation; thiophene S-oxidation→sulfur oxidation; NIH shift / arene-oxide
  rearrangement→arene oxide formation. Scrubbed **131** dangling related_match
  refs to wiped ids. Tool: `tools/drop_aromatic_impact_shelf.py`. Validator 0/0.

- Rehomed **58** unplaced reaction-class terms: **55** placed under chemist
  parents (isoredox / conjugation / hydrolysis / Forest rules / skeletal /
  descriptor process facet); **3** merged as duplicates (deamination→oxidative
  deamination, carbon oxidation→oxidation, C–X oxidative cleavage→dealkylation).
  Nested heteroatom oxidation under SO; dehalogenation umbrella over ox/red.
  Empty unplaced shelf retired. Tool: `tools/rehome_unplaced_rc.py`. Validator 0/0.

- Tree display: Forest **pattern** (+ rule) annotations; inherit nearest ancestor
  pattern on unmapped children; also show tagger SMARTS SSSOM. Reparented
  **alpha-hydroxylation** under methyl/methylene hydroxylation
  (`pattern:Hydroxylation/h2`).

- Forest `forest.rule` / `forest.pattern` SSSOM: **exactMatch or closeMatch**
  only (rulesets stay `relatedMatch`). Upgraded leftover
  `Glutathionation/michael` relatedMatch → exactMatch. EpoxideHydration remains
  closeMatch. Validator enforces for all rule/pattern rows.

- Diagnosis: **46** tagger SMARTS homes sit outside Forest rule/pattern
  ancestry — not expected zero. Causes: (1) **31** parked under `unplaced
  reaction class term` (placement debt; a few have Forest-scoped emits later in
  the list, e.g. alpha-hydroxylation→hydroxylation); (2) **12** CJ-adjacent
  (methylation, amino-acid, NAC/mercapturic, formylation, …) with no Forest
  rule; (3) **3** broad umbrellas (oxidation×2, reduction).

- Forest `forest.rule` SSSOM: upgraded `relatedMatch` → **exactMatch** (27) or
  **closeMatch** (1: EpoxideHydration ↔ epoxide opening). Rulesets stay
  `relatedMatch`. Validator enforces exact/close for all `forest.rule` rows.

- Tagger SMARTS coverage: `data/mappings/xmet-tagger.sssom.tsv` — **150**
  `skos:exactMatch` rows (rule → first live reaction-class emit). Rebuild:
  `make rebuild-tagger-sssom`. Validator requires every SMARTS rule mapped under
  reaction class (`make validate-redesign`). Non-SMARTS tag/delta/forest-tag
  rules deferred (helpers / wiped spines).

- `Hydrogenation/path_end`: not nitrogen — Forest conjugated-path end (adds H,
  dearomatize capability; carbonyl-O end → alcohol). Added as **conjugated-path
  hydrogenation** under hydrogenation with exactMatch. Xfail whitelist empty.
  Validator **0/0**.

- Wiped deferred spines (plan out-of-scope): medchem, reactive, products, site,
  forest-map, provenance, evidence, biological context, ambiguity, product status,
  pharmacological role, annotation about, legacy phase I/II families; also
  disposition sequential/first-pass/intermediate. **562** retired, **367** remain
  (before pattern mints). Live spines: disposition, reaction class, reaction
  descriptor, concept relation. Backup = git. Tool: `tools/drop_deferred_spines.py`.

- Forest pattern SSSOM: chemist homes **must** be `skos:exactMatch`. Gaps from
  `make validate-redesign` guide hand batches (no auto-fix). Done: N-oxidation (3),
  Hydrogenation alkene/alkyne (2), Dephosphorylation (1), SulfurReduction
  sulfoxide/disulfide (2), OxygenReduction/carbonyl, nitro→amine, Dehydrogenation
  alcohol/amine (2), ReductiveDehalogenation (2), Epoxidation/epoxide (1). Endpoints
  xfail (4). Hard gaps remaining: **42** (mostly missing pattern SSSOM after
  forest-map alias scrub).
- Dropped 48 redundant `12001xx`/`13001xx` `* class` duplicates; fixed bad
  aromatic-epoxidation→arene-oxide merge; unplaced ~63.

- Clean reaction-class rebuild (`tools/rebuild_reaction_class_clean.py`): skeleton
  first (oxidation/reduction/isoredox + colors + conjugation fork + rearrangement);
  imported PhaseOneRS **16/16** rules + conjugations; parked rest then rehomed 108
  specializations. Reaction class direct children: 7. Forest SSSOM chemist-preferred
  (163→127). Backup: `artifacts/xmet.yaml.pre-clean-rxn-class.yaml`.

- Redesign v1 apply (spines 1–3 + relation vocab): disposition stage; reaction
  class with **oxidation / reduction / isoredox** near top — SO+UO+DH under
  oxidation, RD as reduction, HD under isoredox; conjugation transfer/adduct
  fork (GSH under adducts); rearrangement nesting; reaction descriptor
  (leaving/ring/cleavage/MetID); concept-relation vocab (`xmet:3xxxxxx`).
- Remap TSV + Forest SSSOM conjugation fork; ChEBI prodrug exact kept.
- Rebuilt exactMatches from [Pistoia UDM](https://github.com/PistoiaAlliance/UDM)
  `udm_6_0_0_reaction_classes.xsd`: require UDM enum + mop.obo name→id (ignore bad
  XSD comments) + **XMET/OBO definition identity**. Retained **10** high-confidence
  exacts (epoxidation, dehalogenation, alkylation, N-alkylation, carboxylation,
  cyclization, halogenation, amination, formylation, arylation). Dropped stubs,
  Phase-II-framed methylation, Rainbow colors, glucuronidation≠glucuronosylation,
  hallucinated RXNO IDs.
- Purged hallucinated soft RXNO/MOP object IDs from external/mop SSSOM (verified
  against rxno.obo / mop.obo names). Regenerated `data/mappings/views/*` including
  `udm_mop_exact.tsv`. Updated `RELATED_ONTOLOGIES.md` for UDM + exactMatch bar.

## 2026-09-27

- Prodrug pipeline alignment: SSSOM `xmet:2300012` ↔ `CHEBI:50266`; synonyms
  for prodrug / active metabolite / CES family; isoform leaves CES1/CES2,
  CYP3A4/CYP3A5 (`xmet:2100232`–`2100235`). Export: 947 concepts.
- Extracted from `xenosite-tagger` via `git filter-repo` (ontology, mappings,
  competency, db_term_mapping, ontology tools) with path history preserved.
- Concept CURIE prefix is `xmet:` (renamed from `xrm:` in tagger tip before extract).
- No RuleSet YAML / rule-bridge here — owned by xenosite-tagger.
