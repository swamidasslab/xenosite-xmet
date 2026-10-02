# BioTransformer ↔ XMET curation

Manual assignment of BioTransformer labels into XMET. **Primary** mapping
targets `reactions.csv` **common_name** stems; MetX class labels are secondary.

## Files

| File | Role |
| --- | --- |
| [`xmet-biotransformer-common.sssom.tsv`](xmet-biotransformer-common.sssom.tsv) | **Primary** SSSOM — `common_name` stems (`bt:<STEM>`) |
| [`xmet-biotransformer.sssom.tsv`](xmet-biotransformer.sssom.tsv) | Secondary SSSOM — MetX `bt.class:*` / `bt.rtype:*` |
| [`biotransformer-proposed-terms.tsv`](biotransformer-proposed-terms.tsv) | Subset types that need a **new XMET child** (with proposed parent) |
| [`biotransformer-unassigned.tsv`](biotransformer-unassigned.tsv) | Examined types not yet placed (site/scaffold / chemistry check) |
| [`biotransformer-excluded.tsv`](biotransformer-excluded.tsv) | Out of XMET xenobiotic scope (see below) |
| [`biotransformer-eawag.tsv`](biotransformer-eawag.tsv) | Opaque EnviPath `EAWAG_RULE_*` ids — deferred; not curated here |
| [`biotransformer-inventory.tsv`](biotransformer-inventory.tsv) | Full type inventory from `xenosite-data` (regenerable) |
| [`biotransformer-rule-smarts.tsv`](biotransformer-rule-smarts.tsv) | Per-pattern reactant SMARTS, exclusion SMARTS, and SMIRKS |

## Placement grains

1. **`bt:*` (primary)** — `reactions.csv` `common_name` (bundles `_PATTERNn`).
   Prefer identity/child matches here.
2. **`bt.rtype:*`** — MetX short `reaction_type` literature classes (often no BTMR).
3. **`bt.class:*`** — MetX `biotransformation_type` (Human Phase I/II, Gut).

## Placement rules

1. **Identity** with an existing XMET term → SSSOM `exactMatch` / `closeMatch`.
2. BT type covers only a **subset** of an XMET term → map to an existing **child**,
   or add a **proposed** leaf under that parent. Never SSSOM-match the parent.
3. Site-only qualifications of an existing head (scaffold / regio) may stay
   **unassigned** until we decide leaf vs annotation bundle.
4. Endogenous pathway encyclopedias, structure-standardization SMIRKS, and
   non-reaction labels → **excluded**.
5. Opaque `EAWAG_RULE_*` rows → **eawag** bucket (no chemist name; skip for now).

## Why exclusions?

XMET is a **xenobiotic** med-chem naming thesaurus ([SCOPE.md](../ontology/SCOPE.md)),
not a general metabolic encyclopedia. BioTransformer’s EC / pathway packs mix
drug-metabolism rules with endogenous lipid, sterol, bile-acid, nucleotide, and
glycosphingolipid chemistry, plus structure-cleanup SMIRKS. Those do not earn
XMET leaves (or SSSOM homes) just because they appear in the KB.

Typical exclude reasons:

| Reason | Examples |
| --- | --- |
| Endogenous lipid / membrane | phosphatidylinositol phosphorylation, ceramide glucosylation, acyl-CoA dehydrogenation |
| Endogenous steroid / bile | sterol hydroxylations/conjugations, bile-acid CoA glycination |
| Endogenous nucleotide / glyco | ribonucleotide dephosphorylation, ganglioside sugar transfer |
| Structure standardization | `*_STANDARDIZATION` SMIRKS (charge/form cleanup, not metabolism) |
| Not a reaction class | cofactor tags (`NADPH-assisted dehydrogenation`), inorganic sulfite reduction |

If a label is *chemically* a xenobiotic reaction but only illustrated on an
endogenous scaffold, prefer **unassigned** (cover vs exclude) over automatic
exclude.

## Refresh inventory

```bash
uv run python tools/inventory_biotransformer.py
uv run python tools/export_biotransformer_rule_smarts.py
make ontology-tree-biotransformer
```

## Status (2026-10-01)

Primary common_name SSSOM seeded (~95 rows) from prior mixed file. Class/rtype
SSSOM retained separately (~33). Named human/gut/base types also in proposed /
unassigned / excluded; EAWAG deferred.
