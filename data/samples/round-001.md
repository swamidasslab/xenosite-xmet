# Proposed terms — feedback round

Regenerate: `cargo run -p xenosite-tagger --example sample_terms -- --write`

Comment inline or open an issue noting the case label + wanted change.

## ethane → ethanol
- reactant: `CC`
- product: `CCO`
- tags: _(none)_
- terms:
  - aliphatic hydroxylation [xmet:0000102] ← xenobiotic biotransformation > phase I > stable oxygenation > hydroxylation > aliphatic hydroxylation
  - hydroxylation [xmet:0000100] ← xenobiotic biotransformation > phase I > stable oxygenation > hydroxylation
  - stable oxygenation [xmet:0000010] ← xenobiotic biotransformation > phase I > stable oxygenation
  - phase I [xmet:0000001] ← xenobiotic biotransformation > phase I
  - xenobiotic biotransformation [xmet:0000000] ← xenobiotic biotransformation

## benzene → phenol
- reactant: `c1ccccc1`
- product: `Oc1ccccc1`
- tags: _(none)_
- terms:
  - aromatic hydroxylation [xmet:0000101] ← xenobiotic biotransformation > phase I > stable oxygenation > hydroxylation > aromatic hydroxylation
  - hydroxylation [xmet:0000100] ← xenobiotic biotransformation > phase I > stable oxygenation > hydroxylation
  - stable oxygenation [xmet:0000010] ← xenobiotic biotransformation > phase I > stable oxygenation
  - phase I [xmet:0000001] ← xenobiotic biotransformation > phase I
  - xenobiotic biotransformation [xmet:0000000] ← xenobiotic biotransformation

## ethene → oxirane
- reactant: `C=C`
- product: `C1CO1`
- tags: _(none)_
- terms:
  - epoxidation [xmet:0000110] ← xenobiotic biotransformation > phase I > stable oxygenation > epoxidation
  - stable oxygenation [xmet:0000010] ← xenobiotic biotransformation > phase I > stable oxygenation
  - phase I [xmet:0000001] ← xenobiotic biotransformation > phase I
  - xenobiotic biotransformation [xmet:0000000] ← xenobiotic biotransformation

## ethanol → acetaldehyde
- reactant: `CCO`
- product: `CC=O`
- tags: _(none)_
- terms:
  - dehydrogenation [xmet:0000012] ← xenobiotic biotransformation > phase I > dehydrogenation
  - phase I [xmet:0000001] ← xenobiotic biotransformation > phase I
  - xenobiotic biotransformation [xmet:0000000] ← xenobiotic biotransformation

## tag: glucuronidation
- reactant: `CCO`
- product: `CCO`
- tags: `forest.rule:Glucuronidation`
- terms:
  - glucuronidation [xmet:0001000] ← xenobiotic biotransformation > phase II > glucuronidation
  - phase II [xmet:0000002] ← xenobiotic biotransformation > phase II
  - xenobiotic biotransformation [xmet:0000000] ← xenobiotic biotransformation

## tag: GSH Michael
- reactant: `C=CC=O`
- product: `C=CC=O`
- tags: `forest.pattern:Glutathionation/michael`
- terms:
  - Michael glutathionation [xmet:0001031] ← xenobiotic biotransformation > phase II > glutathionation > Michael glutathionation
  - glutathionation [xmet:0001030] ← xenobiotic biotransformation > phase II > glutathionation
  - phase II [xmet:0000002] ← xenobiotic biotransformation > phase II
  - xenobiotic biotransformation [xmet:0000000] ← xenobiotic biotransformation

## tag: N-dealkylation
- reactant: `CCN(C)C`
- product: `CCNC`
- tags: `forest.rule:NDealkylation`
- terms:
  - N-dealkylation [xmet:0000201] ← xenobiotic biotransformation > phase I > unstable oxygenation > dealkylation > N-dealkylation
  - dealkylation [xmet:0000200] ← xenobiotic biotransformation > phase I > unstable oxygenation > dealkylation
  - unstable oxygenation [xmet:0000011] ← xenobiotic biotransformation > phase I > unstable oxygenation
  - phase I [xmet:0000001] ← xenobiotic biotransformation > phase I
  - xenobiotic biotransformation [xmet:0000000] ← xenobiotic biotransformation

## tag: quinone formation
- reactant: `c1ccccc1`
- product: `O=C1C=CC(=O)C=C1`
- tags: `forest.rule:QuinoneFormation`
- terms:
  - quinone formation [xmet:0000300] ← xenobiotic biotransformation > phase I > quinone formation
  - phase I [xmet:0000001] ← xenobiotic biotransformation > phase I
  - xenobiotic biotransformation [xmet:0000000] ← xenobiotic biotransformation

