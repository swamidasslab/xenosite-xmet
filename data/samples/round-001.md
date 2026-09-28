# Proposed terms — feedback round

Regenerate: `cargo run -p xenosite-tagger --example sample_terms -- --write`

Comment inline or open an issue noting the case label + wanted change.

## ethane → ethanol
- reactant: `CC`
- product: `CCO`
- tags: _(none)_
- terms:
  - aliphatic hydroxylation [xmet:4000014] ← xenobiotic biotransformation > phase I > stable oxygenation > hydroxylation > aliphatic hydroxylation
  - hydroxylation [xmet:4000012] ← xenobiotic biotransformation > phase I > stable oxygenation > hydroxylation
  - stable oxygenation [xmet:4000004] ← xenobiotic biotransformation > phase I > stable oxygenation
  - phase I [xmet:4000001] ← xenobiotic biotransformation > phase I
  - xenobiotic biotransformation [xmet:4000000] ← xenobiotic biotransformation

## benzene → phenol
- reactant: `c1ccccc1`
- product: `Oc1ccccc1`
- tags: _(none)_
- terms:
  - aromatic hydroxylation [xmet:4000013] ← xenobiotic biotransformation > phase I > stable oxygenation > hydroxylation > aromatic hydroxylation
  - hydroxylation [xmet:4000012] ← xenobiotic biotransformation > phase I > stable oxygenation > hydroxylation
  - stable oxygenation [xmet:4000004] ← xenobiotic biotransformation > phase I > stable oxygenation
  - phase I [xmet:4000001] ← xenobiotic biotransformation > phase I
  - xenobiotic biotransformation [xmet:4000000] ← xenobiotic biotransformation

## ethene → oxirane
- reactant: `C=C`
- product: `C1CO1`
- tags: _(none)_
- terms:
  - epoxidation [xmet:4000022] ← xenobiotic biotransformation > phase I > stable oxygenation > epoxidation
  - stable oxygenation [xmet:4000004] ← xenobiotic biotransformation > phase I > stable oxygenation
  - phase I [xmet:4000001] ← xenobiotic biotransformation > phase I
  - xenobiotic biotransformation [xmet:4000000] ← xenobiotic biotransformation

## ethanol → acetaldehyde
- reactant: `CCO`
- product: `CC=O`
- tags: _(none)_
- terms:
  - dehydrogenation [xmet:4000006] ← xenobiotic biotransformation > phase I > dehydrogenation
  - phase I [xmet:4000001] ← xenobiotic biotransformation > phase I
  - xenobiotic biotransformation [xmet:4000000] ← xenobiotic biotransformation

## tag: glucuronidation
- reactant: `CCO`
- product: `CCO`
- tags: `forest.rule:Glucuronidation`
- terms:
  - glucuronidation [xmet:4000148] ← xenobiotic biotransformation > phase II > glucuronidation
  - phase II [xmet:4000002] ← xenobiotic biotransformation > phase II
  - xenobiotic biotransformation [xmet:4000000] ← xenobiotic biotransformation

## tag: GSH Michael
- reactant: `C=CC=O`
- product: `C=CC=O`
- tags: `forest.pattern:Glutathionation/michael`
- terms:
  - Michael glutathionation [xmet:4000168] ← xenobiotic biotransformation > phase II > glutathionation > Michael glutathionation
  - glutathionation [xmet:4000167] ← xenobiotic biotransformation > phase II > glutathionation
  - phase II [xmet:4000002] ← xenobiotic biotransformation > phase II
  - xenobiotic biotransformation [xmet:4000000] ← xenobiotic biotransformation

## tag: N-dealkylation
- reactant: `CCN(C)C`
- product: `CCNC`
- tags: `forest.rule:NDealkylation`
- terms:
  - N-dealkylation [xmet:4000043] ← xenobiotic biotransformation > phase I > unstable oxygenation > dealkylation > N-dealkylation
  - dealkylation [xmet:4000042] ← xenobiotic biotransformation > phase I > unstable oxygenation > dealkylation
  - unstable oxygenation [xmet:4000005] ← xenobiotic biotransformation > phase I > unstable oxygenation
  - phase I [xmet:4000001] ← xenobiotic biotransformation > phase I
  - xenobiotic biotransformation [xmet:4000000] ← xenobiotic biotransformation

## tag: quinone formation
- reactant: `c1ccccc1`
- product: `O=C1C=CC(=O)C=C1`
- tags: `forest.rule:QuinoneFormation`
- terms:
  - quinone formation [xmet:4000059] ← xenobiotic biotransformation > phase I > quinone formation
  - phase I [xmet:4000001] ← xenobiotic biotransformation > phase I
  - xenobiotic biotransformation [xmet:4000000] ← xenobiotic biotransformation

