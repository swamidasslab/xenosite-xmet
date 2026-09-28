# Proposed terms — feedback round 002

Forest-mapped Phase I class parents use full names (stable/unstable oxygenation, dehydrogenation, hydrolysis, reduction). Leaves and facets from Rainbow (21 types), Metabolic Forest (conjugation / quinone / tautomerization), and the quinone-formation paper (species + one-/two-step). No SO/UO/DH/HD/RD as XMET labels.

Regenerate: `cargo run -p xenosite-tagger --example sample_terms -- --write`

## ethane → ethanol (aliphatic hydroxylation)
- reactant: `CC`
- product: `CCO`
- tags: _(none)_
- terms:
  - aliphatic hydroxylation [xmet:4000014] ← xenobiotic biotransformation > phase I > stable oxygenation > hydroxylation > aliphatic hydroxylation
  - carbon oxidation [xmet:4000009] ← xenobiotic biotransformation > phase I > oxidation > carbon oxidation
  - hydroxylation [xmet:4000012] ← xenobiotic biotransformation > phase I > stable oxygenation > hydroxylation
  - oxidation [xmet:4000009] ← xenobiotic biotransformation > phase I > oxidation
  - stable oxygenation [xmet:4000004] ← xenobiotic biotransformation > phase I > stable oxygenation
  - phase I [xmet:4000001] ← xenobiotic biotransformation > phase I
  - xenobiotic biotransformation [xmet:4000000] ← xenobiotic biotransformation

## benzene → phenol (aromatic hydroxylation)
- reactant: `c1ccccc1`
- product: `Oc1ccccc1`
- tags: _(none)_
- terms:
  - aromatic hydroxylation [xmet:4000013] ← xenobiotic biotransformation > phase I > stable oxygenation > hydroxylation > aromatic hydroxylation
  - carbon oxidation [xmet:4000009] ← xenobiotic biotransformation > phase I > oxidation > carbon oxidation
  - hydroxylation [xmet:4000012] ← xenobiotic biotransformation > phase I > stable oxygenation > hydroxylation
  - oxidation [xmet:4000009] ← xenobiotic biotransformation > phase I > oxidation
  - stable oxygenation [xmet:4000004] ← xenobiotic biotransformation > phase I > stable oxygenation
  - phase I [xmet:4000001] ← xenobiotic biotransformation > phase I
  - xenobiotic biotransformation [xmet:4000000] ← xenobiotic biotransformation

## chem:para-hydroxylation
- reactant: `CCc1ccccc1`
- product: `CCc1ccc(O)cc1`
- tags: `chem:para-hydroxylation`, `chem:aromatic-hydroxylation`
- terms:
  - para-hydroxylation [xmet:4000015] ← xenobiotic biotransformation > phase I > stable oxygenation > hydroxylation > aromatic hydroxylation > para-hydroxylation
  - aromatic hydroxylation [xmet:4000013] ← xenobiotic biotransformation > phase I > stable oxygenation > hydroxylation > aromatic hydroxylation
  - carbon oxidation [xmet:4000009] ← xenobiotic biotransformation > phase I > oxidation > carbon oxidation
  - hydroxylation [xmet:4000012] ← xenobiotic biotransformation > phase I > stable oxygenation > hydroxylation
  - oxidation [xmet:4000009] ← xenobiotic biotransformation > phase I > oxidation
  - stable oxygenation [xmet:4000004] ← xenobiotic biotransformation > phase I > stable oxygenation
  - phase I [xmet:4000001] ← xenobiotic biotransformation > phase I
  - xenobiotic biotransformation [xmet:4000000] ← xenobiotic biotransformation

## chem:benzylic-hydroxylation
- reactant: `CCc1ccccc1`
- product: `CC(O)c1ccccc1`
- tags: `chem:benzylic-hydroxylation`
- terms:
  - aliphatic hydroxylation [xmet:4000014] ← xenobiotic biotransformation > phase I > stable oxygenation > hydroxylation > aliphatic hydroxylation
  - benzylic hydroxylation [xmet:4000018] ← xenobiotic biotransformation > phase I > stable oxygenation > hydroxylation > benzylic hydroxylation
  - carbon oxidation [xmet:4000009] ← xenobiotic biotransformation > phase I > oxidation > carbon oxidation
  - hydroxylation [xmet:4000012] ← xenobiotic biotransformation > phase I > stable oxygenation > hydroxylation
  - oxidation [xmet:4000009] ← xenobiotic biotransformation > phase I > oxidation
  - stable oxygenation [xmet:4000004] ← xenobiotic biotransformation > phase I > stable oxygenation
  - phase I [xmet:4000001] ← xenobiotic biotransformation > phase I
  - xenobiotic biotransformation [xmet:4000000] ← xenobiotic biotransformation

## ethene → oxirane
- reactant: `C=C`
- product: `C1CO1`
- tags: _(none)_
- terms:
  - alkene epoxidation [xmet:4000023] ← xenobiotic biotransformation > phase I > stable oxygenation > epoxidation > alkene epoxidation
  - carbon oxidation [xmet:4000009] ← xenobiotic biotransformation > phase I > oxidation > carbon oxidation
  - epoxidation [xmet:4000022] ← xenobiotic biotransformation > phase I > stable oxygenation > epoxidation
  - oxidation [xmet:4000009] ← xenobiotic biotransformation > phase I > oxidation
  - stable oxygenation [xmet:4000004] ← xenobiotic biotransformation > phase I > stable oxygenation
  - phase I [xmet:4000001] ← xenobiotic biotransformation > phase I
  - xenobiotic biotransformation [xmet:4000000] ← xenobiotic biotransformation

## chem:arene-oxide + NIH-shift facets
- reactant: `c1ccccc1`
- product: `Oc1ccccc1`
- tags: `chem:arene-oxide`, `chem:NIH-shift`
- terms:
  - arene oxide formation [xmet:4000024] ← xenobiotic biotransformation > phase I > stable oxygenation > epoxidation > arene oxide formation
  - aromatic hydroxylation [xmet:4000013] ← xenobiotic biotransformation > phase I > stable oxygenation > hydroxylation > aromatic hydroxylation
  - carbon oxidation [xmet:4000009] ← xenobiotic biotransformation > phase I > oxidation > carbon oxidation
  - epoxidation [xmet:4000022] ← xenobiotic biotransformation > phase I > stable oxygenation > epoxidation
  - hydroxylation [xmet:4000012] ← xenobiotic biotransformation > phase I > stable oxygenation > hydroxylation
  - NIH shift [xmet:4000197] ← xenobiotic biotransformation > process facet > NIH shift
  - dearomatization [xmet:4000194] ← xenobiotic biotransformation > process facet > dearomatization
  - oxidation [xmet:4000009] ← xenobiotic biotransformation > phase I > oxidation
  - rearomatization [xmet:4000195] ← xenobiotic biotransformation > process facet > rearomatization
  - stable oxygenation [xmet:4000004] ← xenobiotic biotransformation > phase I > stable oxygenation
  - phase I [xmet:4000001] ← xenobiotic biotransformation > phase I
  - process facet [xmet:0004000] ← xenobiotic biotransformation > process facet
  - xenobiotic biotransformation [xmet:4000000] ← xenobiotic biotransformation

## ethanol → acetaldehyde
- reactant: `CCO`
- product: `CC=O`
- tags: _(none)_
- terms:
  - primary alcohol oxidation [xmet:4000070] ← xenobiotic biotransformation > phase I > dehydrogenation > alcohol oxidation > primary alcohol oxidation
  - alcohol oxidation [xmet:4000069] ← xenobiotic biotransformation > phase I > dehydrogenation > alcohol oxidation
  - carbon oxidation [xmet:4000009] ← xenobiotic biotransformation > phase I > oxidation > carbon oxidation
  - dehydrogenation [xmet:4000006] ← xenobiotic biotransformation > phase I > dehydrogenation
  - oxidation [xmet:4000009] ← xenobiotic biotransformation > phase I > oxidation
  - phase I [xmet:4000001] ← xenobiotic biotransformation > phase I
  - xenobiotic biotransformation [xmet:4000000] ← xenobiotic biotransformation

## chem:N-demethylation
- reactant: `CN(C)C`
- product: `CNC`
- tags: `chem:N-demethylation`
- terms:
  - N-demethylation [xmet:4000349] ← xenobiotic biotransformation > phase I > unstable oxygenation > dealkylation > N-dealkylation > N-demethylation
  - N-dealkylation [xmet:4000043] ← xenobiotic biotransformation > phase I > unstable oxygenation > dealkylation > N-dealkylation
  - carbon–heteroatom oxidative cleavage [xmet:4000042] ← xenobiotic biotransformation > phase I > oxidation > carbon–heteroatom oxidative cleavage
  - dealkylation [xmet:4000042] ← xenobiotic biotransformation > phase I > unstable oxygenation > dealkylation
  - carbinolamine cleavage [xmet:4000198] ← xenobiotic biotransformation > process facet > carbinolamine cleavage
  - oxidation [xmet:4000009] ← xenobiotic biotransformation > phase I > oxidation
  - unstable oxygenation [xmet:4000005] ← xenobiotic biotransformation > phase I > unstable oxygenation
  - phase I [xmet:4000001] ← xenobiotic biotransformation > phase I
  - process facet [xmet:0004000] ← xenobiotic biotransformation > process facet
  - xenobiotic biotransformation [xmet:4000000] ← xenobiotic biotransformation

## chem:oxidative-deamination
- reactant: `CCN`
- product: `CC=O`
- tags: `chem:oxidative-deamination`
- terms:
  - oxidative deamination [xmet:4000049] ← xenobiotic biotransformation > phase I > unstable oxygenation > dealkylation > N-dealkylation > oxidative deamination
  - N-dealkylation [xmet:4000043] ← xenobiotic biotransformation > phase I > unstable oxygenation > dealkylation > N-dealkylation
  - carbon–heteroatom oxidative cleavage [xmet:4000042] ← xenobiotic biotransformation > phase I > oxidation > carbon–heteroatom oxidative cleavage
  - dealkylation [xmet:4000042] ← xenobiotic biotransformation > phase I > unstable oxygenation > dealkylation
  - carbinolamine cleavage [xmet:4000198] ← xenobiotic biotransformation > process facet > carbinolamine cleavage
  - oxidation [xmet:4000009] ← xenobiotic biotransformation > phase I > oxidation
  - unstable oxygenation [xmet:4000005] ← xenobiotic biotransformation > phase I > unstable oxygenation
  - phase I [xmet:4000001] ← xenobiotic biotransformation > phase I
  - process facet [xmet:0004000] ← xenobiotic biotransformation > process facet
  - xenobiotic biotransformation [xmet:4000000] ← xenobiotic biotransformation

## chem:O-demethylation
- reactant: `COc1ccccc1`
- product: `Oc1ccccc1`
- tags: `chem:O-demethylation`
- terms:
  - O-demethylation [xmet:4000050] ← xenobiotic biotransformation > phase I > unstable oxygenation > dealkylation > O-dealkylation > O-demethylation
  - O-dealkylation [xmet:4000044] ← xenobiotic biotransformation > phase I > unstable oxygenation > dealkylation > O-dealkylation
  - carbon–heteroatom oxidative cleavage [xmet:4000042] ← xenobiotic biotransformation > phase I > oxidation > carbon–heteroatom oxidative cleavage
  - dealkylation [xmet:4000042] ← xenobiotic biotransformation > phase I > unstable oxygenation > dealkylation
  - oxidation [xmet:4000009] ← xenobiotic biotransformation > phase I > oxidation
  - unstable oxygenation [xmet:4000005] ← xenobiotic biotransformation > phase I > unstable oxygenation
  - phase I [xmet:4000001] ← xenobiotic biotransformation > phase I
  - xenobiotic biotransformation [xmet:4000000] ← xenobiotic biotransformation

## chem:acyl-glucuronidation
- reactant: `CC(=O)O`
- product: `CC(=O)O`
- tags: `chem:acyl-glucuronidation`
- terms:
  - acyl glucuronidation [xmet:4000152] ← xenobiotic biotransformation > phase II > glucuronidation > O-glucuronidation > acyl glucuronidation
  - O-glucuronidation [xmet:4000149] ← xenobiotic biotransformation > phase II > glucuronidation > O-glucuronidation
  - alcohol oxidation [xmet:4000069] ← xenobiotic biotransformation > phase I > dehydrogenation > alcohol oxidation
  - carbon oxidation [xmet:4000009] ← xenobiotic biotransformation > phase I > oxidation > carbon oxidation
  - acyl migration [xmet:4000209] ← xenobiotic biotransformation > process facet > acyl migration
  - dehydrogenation [xmet:4000006] ← xenobiotic biotransformation > phase I > dehydrogenation
  - glucuronidation [xmet:4000148] ← xenobiotic biotransformation > phase II > glucuronidation
  - oxidation [xmet:4000009] ← xenobiotic biotransformation > phase I > oxidation
  - phase I [xmet:4000001] ← xenobiotic biotransformation > phase I
  - phase II [xmet:4000002] ← xenobiotic biotransformation > phase II
  - process facet [xmet:0004000] ← xenobiotic biotransformation > process facet
  - xenobiotic biotransformation [xmet:4000000] ← xenobiotic biotransformation

## chem:phenolic-glucuronidation
- reactant: `Oc1ccccc1`
- product: `Oc1ccccc1`
- tags: `chem:phenolic-glucuronidation`
- terms:
  - phenolic glucuronidation [xmet:4000150] ← xenobiotic biotransformation > phase II > glucuronidation > O-glucuronidation > phenolic glucuronidation
  - O-glucuronidation [xmet:4000149] ← xenobiotic biotransformation > phase II > glucuronidation > O-glucuronidation
  - glucuronidation [xmet:4000148] ← xenobiotic biotransformation > phase II > glucuronidation
  - phase II [xmet:4000002] ← xenobiotic biotransformation > phase II
  - xenobiotic biotransformation [xmet:4000000] ← xenobiotic biotransformation

## chem:GSH-Michael + conjugate-addition facet
- reactant: `C=CC=O`
- product: `C=CC=O`
- tags: `chem:GSH-Michael`
- terms:
  - Michael glutathionation [xmet:4000168] ← xenobiotic biotransformation > phase II > glutathionation > Michael glutathionation
  - conjugate addition [xmet:4000206] ← xenobiotic biotransformation > process facet > conjugate addition
  - glutathionation [xmet:4000167] ← xenobiotic biotransformation > phase II > glutathionation
  - phase II [xmet:4000002] ← xenobiotic biotransformation > phase II
  - process facet [xmet:0004000] ← xenobiotic biotransformation > process facet
  - xenobiotic biotransformation [xmet:4000000] ← xenobiotic biotransformation

## chem:quinone-formation (dearomatization + bioactivation)
- reactant: `c1ccccc1`
- product: `O=C1C=CC(=O)C=C1`
- tags: `chem:quinone-formation`
- terms:
  - quinone formation [xmet:4000059] ← xenobiotic biotransformation > phase I > dehydrogenation > quinone formation
  - dearomatization [xmet:4000194] ← xenobiotic biotransformation > process facet > dearomatization
  - dehydrogenation [xmet:4000006] ← xenobiotic biotransformation > phase I > dehydrogenation
  - bioactivation [xmet:0003000] ← xenobiotic biotransformation > bioactivation
  - phase I [xmet:4000001] ← xenobiotic biotransformation > phase I
  - process facet [xmet:0004000] ← xenobiotic biotransformation > process facet
  - xenobiotic biotransformation [xmet:4000000] ← xenobiotic biotransformation

## chem:quinone-imine + one-step quinone formation
- reactant: `CC(=O)Nc1ccc(O)cc1`
- product: `CC(=O)N=C1C=CC(=O)C=C1`
- tags: `chem:quinone-imine`, `chem:one-step-quinone-formation`
- terms:
  - one-step quinone formation [xmet:4000066] ← xenobiotic biotransformation > phase I > dehydrogenation > quinone formation > one-step quinone formation
  - quinone-imine formation [xmet:4000062] ← xenobiotic biotransformation > phase I > dehydrogenation > quinone formation > quinone-imine formation
  - alcohol oxidation [xmet:4000069] ← xenobiotic biotransformation > phase I > dehydrogenation > alcohol oxidation
  - carbon oxidation [xmet:4000009] ← xenobiotic biotransformation > phase I > oxidation > carbon oxidation
  - quinone formation [xmet:4000059] ← xenobiotic biotransformation > phase I > dehydrogenation > quinone formation
  - dearomatization [xmet:4000194] ← xenobiotic biotransformation > process facet > dearomatization
  - dehydrogenation [xmet:4000006] ← xenobiotic biotransformation > phase I > dehydrogenation
  - oxidation [xmet:4000009] ← xenobiotic biotransformation > phase I > oxidation
  - bioactivation [xmet:0003000] ← xenobiotic biotransformation > bioactivation
  - phase I [xmet:4000001] ← xenobiotic biotransformation > phase I
  - process facet [xmet:0004000] ← xenobiotic biotransformation > process facet
  - xenobiotic biotransformation [xmet:4000000] ← xenobiotic biotransformation

## chem:two-step-quinone-formation
- reactant: `c1ccccc1`
- product: `O=C1C=CC(=O)C=C1`
- tags: `chem:two-step-quinone-formation`
- terms:
  - two-step quinone formation [xmet:4000067] ← xenobiotic biotransformation > phase I > dehydrogenation > quinone formation > two-step quinone formation
  - quinone formation [xmet:4000059] ← xenobiotic biotransformation > phase I > dehydrogenation > quinone formation
  - dearomatization [xmet:4000194] ← xenobiotic biotransformation > process facet > dearomatization
  - dehydrogenation [xmet:4000006] ← xenobiotic biotransformation > phase I > dehydrogenation
  - bioactivation [xmet:0003000] ← xenobiotic biotransformation > bioactivation
  - phase I [xmet:4000001] ← xenobiotic biotransformation > phase I
  - process facet [xmet:0004000] ← xenobiotic biotransformation > process facet
  - xenobiotic biotransformation [xmet:4000000] ← xenobiotic biotransformation

## chem:imine-methide
- reactant: `Nc1ccc(C)cc1`
- product: `N=C1C=CC(=C)C=C1`
- tags: `chem:imine-methide`
- terms:
  - imine-methide formation [xmet:4000065] ← xenobiotic biotransformation > phase I > dehydrogenation > quinone formation > imine-methide formation
  - quinone formation [xmet:4000059] ← xenobiotic biotransformation > phase I > dehydrogenation > quinone formation
  - dearomatization [xmet:4000194] ← xenobiotic biotransformation > process facet > dearomatization
  - dehydrogenation [xmet:4000006] ← xenobiotic biotransformation > phase I > dehydrogenation
  - bioactivation [xmet:0003000] ← xenobiotic biotransformation > bioactivation
  - phase I [xmet:4000001] ← xenobiotic biotransformation > phase I
  - process facet [xmet:0004000] ← xenobiotic biotransformation > process facet
  - xenobiotic biotransformation [xmet:4000000] ← xenobiotic biotransformation

## chem:dearomatization alone
- reactant: `c1ccccc1`
- product: `C1=CC=CC=C1`
- tags: `chem:dearomatization`
- terms:
  - dearomatization [xmet:4000194] ← xenobiotic biotransformation > process facet > dearomatization
  - process facet [xmet:0004000] ← xenobiotic biotransformation > process facet
  - xenobiotic biotransformation [xmet:4000000] ← xenobiotic biotransformation

## chem:nitroaromatic-reduction
- reactant: `O=[N+]([O-])c1ccccc1`
- product: `Nc1ccccc1`
- tags: `chem:nitroaromatic-reduction`
- terms:
  - nitroaromatic reduction [xmet:4000096] ← xenobiotic biotransformation > phase I > reduction > nitrogen reduction > nitro reduction > nitroaromatic reduction
  - nitro reduction [xmet:4000094] ← xenobiotic biotransformation > phase I > reduction > nitrogen reduction > nitro reduction
  - nitrogen reduction [xmet:4000093] ← xenobiotic biotransformation > phase I > reduction > nitrogen reduction
  - reduction [xmet:4000008] ← xenobiotic biotransformation > phase I > reduction
  - bioactivation [xmet:0003000] ← xenobiotic biotransformation > bioactivation
  - phase I [xmet:4000001] ← xenobiotic biotransformation > phase I
  - xenobiotic biotransformation [xmet:4000000] ← xenobiotic biotransformation

## chem:cyanide-hydrolysis
- reactant: `CC#N`
- product: `CC(=O)O`
- tags: `chem:cyanide-hydrolysis`
- terms:
  - cyanide hydrolysis [xmet:4000086] ← xenobiotic biotransformation > phase I > hydrolysis > cyanide hydrolysis
  - hydrolysis [xmet:4000007] ← xenobiotic biotransformation > phase I > hydrolysis
  - phase I [xmet:4000001] ← xenobiotic biotransformation > phase I
  - xenobiotic biotransformation [xmet:4000000] ← xenobiotic biotransformation

## chem:carbonyl-reduction
- reactant: `CC(=O)C`
- product: `CC(O)C`
- tags: `chem:carbonyl-reduction`
- terms:
  - carbonyl reduction [xmet:4000105] ← xenobiotic biotransformation > phase I > reduction > oxygen reduction > carbonyl reduction
  - oxygen reduction [xmet:4000101] ← xenobiotic biotransformation > phase I > reduction > oxygen reduction
  - reduction [xmet:4000008] ← xenobiotic biotransformation > phase I > reduction
  - phase I [xmet:4000001] ← xenobiotic biotransformation > phase I
  - xenobiotic biotransformation [xmet:4000000] ← xenobiotic biotransformation

## chem:glycine-conjugation
- reactant: `c1ccccc1C(=O)O`
- product: `c1ccccc1C(=O)O`
- tags: `chem:glycine-conjugation`
- terms:
  - alcohol oxidation [xmet:4000069] ← xenobiotic biotransformation > phase I > dehydrogenation > alcohol oxidation
  - carbon oxidation [xmet:4000009] ← xenobiotic biotransformation > phase I > oxidation > carbon oxidation
  - glycine conjugation [xmet:4000180] ← xenobiotic biotransformation > phase II > amino acid conjugation > glycine conjugation
  - amino acid conjugation [xmet:4000179] ← xenobiotic biotransformation > phase II > amino acid conjugation
  - dehydrogenation [xmet:4000006] ← xenobiotic biotransformation > phase I > dehydrogenation
  - oxidation [xmet:4000009] ← xenobiotic biotransformation > phase I > oxidation
  - phase I [xmet:4000001] ← xenobiotic biotransformation > phase I
  - phase II [xmet:4000002] ← xenobiotic biotransformation > phase II
  - xenobiotic biotransformation [xmet:4000000] ← xenobiotic biotransformation

## chem:tautomerization
- reactant: `CC(=O)C`
- product: `CC(O)=C`
- tags: `chem:tautomerization`
- terms:
  - tautomerization [xmet:4000186] ← xenobiotic biotransformation > tautomerization
  - xenobiotic biotransformation [xmet:4000000] ← xenobiotic biotransformation

