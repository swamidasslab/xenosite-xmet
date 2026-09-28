# XMET ontology tree (2–3 levels) — prune review

Generated from local `data/ontology/xmet.yaml` for external review.
Shows each **spine**, then up to ~15 children, then a short grandchild summary.
Deeper leaves are collapsed as `+N more`. Cross-spine multi-parents are not duplicated.

**Root:** xenobiotic biotransformation (`xmet:4000000`)

## metabolism phase (`xmet:4000212`, ~192 descendants)

> Phase framing for xenobiotic biotransformation (I / II / III).

- first-pass metabolism (`xmet:1000102`)
- intermediate metabolite formation (`xmet:1000101`)
- **phase I** (`xmet:4000001`)
  - deacetylation (`xmet:4000166`)
  - deacylation (`xmet:4000191`)
  - decarbonylation (`xmet:4000193`)
  - dehydration (`xmet:4000113`)
  - dehydrogenation (`xmet:4000006`): alcohol oxidation, alkene formation, aromatization, double- to triple-bond dehydrogenation, iminium ion formation, single- to double-bond dehydrogenation
  - denitrogenation (`xmet:4000192`)
  - hydrolysis (`xmet:4000007`): amide hydrolysis, azo cleavage, carbamate hydrolysis, cyanide hydrolysis, deacetylation, deconjugation, +11 more
  - oxidation (`xmet:4000009`): carbon oxidation, carbon–heteroatom oxidative cleavage, heteroatom oxidation, oxidative dehalogenation
  - … +2 more under phase I
- **phase II** (`xmet:4000002`)
  - acetylation (`xmet:4000163`): N-acetylation, O-acetylation
  - acyl glucuronidation class (`xmet:4000152`)
  - amino acid conjugation (`xmet:4000179`): glutamine conjugation, glycine conjugation, serine conjugation, taurine conjugation
  - C-glucuronidation class (`xmet:4000156`)
  - carbamoyl glucuronidation class (`xmet:4000157`)
  - CoA conjugation (`xmet:4000185`)
  - cysteine conjugation (`xmet:4000217`)
  - epoxide GSH conjugation (`xmet:4000169`)
  - … +28 more under phase II
- phase III transport (`xmet:4000003`)
- sequential metabolism (`xmet:1000100`)

## chemical transformation (`xmet:4000213`, ~164 descendants)

> Enzyme-independent chemical edit class (oxidation, reduction, …).

- **alkylation** (`xmet:4000116`)
  - C-alkylation (`xmet:4000120`)
  - N-alkylation (`xmet:4000117`)
  - O-alkylation (`xmet:4000118`)
  - S-alkylation (`xmet:4000119`)
- amination (`xmet:4000130`)
- aromatization (`xmet:4000074`)
- arylation (`xmet:4000145`)
- carbonylation (`xmet:4000146`)
- carboxylation (`xmet:4000122`)
- conjugation (`xmet:4000011`)
- cyanidation (`xmet:4000114`)
- cyclization (`xmet:4000127`)
- **dealkylation** (`xmet:4000042`)
  - C-dealkylation (`xmet:4000046`)
  - dearylation (`xmet:4000143`)
  - N-dealkylation (`xmet:4000043`): N-deethylation, N-demethylation, N-depropylation, oxidative deamination
  - O-dealkylation (`xmet:4000044`): aliphatic O-dealkylation, aromatic O-dealkylation, O-deethylation, O-demethylation
  - S-dealkylation (`xmet:4000045`): S-demethylation
- deamination (`xmet:4000049`)
- **dearomatization** (`xmet:4000194`)
  - thiophene S-oxidation (`xmet:4000035`)
- decarboxylation (`xmet:4000121`)
- deconjugation (`xmet:4000147`)
- decyanidation (`xmet:4000115`)
- … +31 more direct children

## phase I reaction family (`xmet:1200000`, ~136 descendants)

> Rainbow-anchored Phase I reaction classes and detailed types.

- alcohol dehydrogenation (`xmet:4000069`)
- aldehyde formation class (`xmet:4000069`)
- aliphatic epoxidation (`xmet:4000215`)
- aliphatic hydroxylation class (`xmet:4000014`)
- amide hydrolysis class (`xmet:4000079`)
- amine dehydrogenation (`xmet:4000216`)
- aromatic epoxidation (`xmet:4000287`)
- aromatic hydroxylation class (`xmet:4000013`)
- C-dealkylation class (`xmet:4000046`)
- carbonyl reduction class (`xmet:4000105`)
- cyanide hydrolysis class (`xmet:4000086`)
- **dehydrogenation** (`xmet:4000006`)
  - alcohol oxidation (`xmet:4000069`): primary alcohol oxidation, secondary alcohol oxidation
  - alkene formation (`xmet:4000073`)
  - aromatization (`xmet:4000074`)
  - double- to triple-bond dehydrogenation (`xmet:4000076`)
  - iminium ion formation (`xmet:4000064`)
  - single- to double-bond dehydrogenation (`xmet:4000075`)
- double-to-triple bond dehydrogenation class (`xmet:4000076`)
- ester hydrolysis class (`xmet:4000078`)
- ether hydrolysis class (`xmet:4000085`)
- … +19 more direct children

## phase II conjugation family (`xmet:1300000`, ~64 descendants)

> Conjugation families typical of Phase II xenobiotic metabolism.

- **acetylation** (`xmet:4000163`)
  - N-acetylation (`xmet:4000164`)
  - O-acetylation (`xmet:4000165`)
- acyl glucuronidation class (`xmet:4000152`)
- **amino acid conjugation** (`xmet:4000179`)
  - glutamine conjugation (`xmet:4000181`)
  - glycine conjugation (`xmet:4000180`)
  - serine conjugation (`xmet:4000183`)
  - taurine conjugation (`xmet:4000182`)
- C-glucuronidation class (`xmet:4000156`)
- carbamoyl glucuronidation class (`xmet:4000157`)
- CoA conjugation (`xmet:4000185`)
- cysteine conjugation (`xmet:4000217`)
- epoxide GSH conjugation (`xmet:4000169`)
- formylation (`xmet:4000131`)
- **glucuronidation** (`xmet:4000148`)
  - C-glucuronidation (`xmet:4000156`)
  - carbamoyl glucuronidation (`xmet:4000157`)
  - N-glucuronidation (`xmet:4000153`): quaternary N-glucuronidation
  - O-glucuronidation (`xmet:4000149`): acyl glucuronidation, alcoholic glucuronidation, phenolic glucuronidation
  - S-glucuronidation (`xmet:4000155`)
- glutamine conjugation class (`xmet:4000181`)
- **glutathionation** (`xmet:4000167`)
  - aziridine glutathionation (`xmet:4000172`)
  - epoxide glutathionation (`xmet:4000169`)
  - halide displacement glutathionation (`xmet:4000170`)
  - isocyanate glutathionation (`xmet:4000171`)
  - mercapturic acid formation (`xmet:4000174`)
  - Michael glutathionation (`xmet:4000168`)
  - quinone glutathionation (`xmet:4000173`)
- glycine conjugation (`xmet:4000180`)
- glycine conjugation class (`xmet:4000180`)
- glycosylation (`xmet:4000184`)
- … +22 more direct children

## medchem liability (`xmet:1400000`, ~51 descendants)

> Medicinal-chemistry liability and design handles for a reaction.

- active metabolite opportunity (`xmet:1400126`)
- acyl glucuronide risk (`xmet:1400121`)
- aldehyde forming (`xmet:1400022`)
- aldehyde risk (`xmet:1400122`)
- amide soft spot (`xmet:1400106`)
- amine soft spot (`xmet:1400102`)
- aromatic soft spot (`xmet:1400100`)
- benzylic soft spot (`xmet:1400101`)
- **bioactivation** (`xmet:0003000`)
  - reactive metabolite formation (`xmet:0003002`)
- **bioactivation** (`xmet:1400012`)
  - bioactivation (`xmet:0003000`): reactive metabolite formation
- bioactivation hotspot (`xmet:1400108`)
- bioactivation risk (`xmet:1400019`)
- clearance hotspot (`xmet:1400107`)
- clearance liability (`xmet:1400011`)
- clearance pathway (`xmet:1400020`)
- … +32 more direct children

## reactive metabolite family (`xmet:1500000`, ~61 descendants)

> Reactive or trapping-prone metabolite product families.

- acyl glucuronide (`xmet:1500015`)
- acyl glucuronide reactive (`xmet:1500107`)
- aldehyde (`xmet:1500013`)
- aldehyde metabolite (`xmet:1500129`)
- arene oxide (`xmet:1500105`)
- aziridine metabolite (`xmet:1500132`)
- benzylic radical (`xmet:1500205`)
- carbinolamine intermediate (`xmet:1500126`)
- carbocation intermediate (`xmet:1500204`)
- carboxylic acid glucuronide (`xmet:1500213`)
- CoA conjugate (`xmet:1500222`)
- covalent binding (`xmet:1500234`)
- cysteine adduct (`xmet:1500218`)
- DNA binding (`xmet:1500231`)
- **electrophile role** (`xmet:7500000`)
  - electrophile consumption (`xmet:7500002`)
  - electrophile generation (`xmet:7500001`)
  - electrophile role unspecified (`xmet:7500005`)
  - nucleophile exposure (`xmet:7500003`)
  - reactivity-neutral step (`xmet:7500004`)
- … +38 more direct children

## metabolite product family (`xmet:2500000`, ~30 descendants)

> Stable or ordinary metabolite product classes (conjugates, oxygenated products, dealkylation products, …). Distinct from reactive / trapping-prone species.

- acetylated metabolite (`xmet:1500224`)
- alcohol metabolite (`xmet:1500120`)
- aminophenol metabolite (`xmet:1500201`)
- carboxylic acid from alcohol (`xmet:1500228`)
- carboxylic acid metabolite (`xmet:1500121`)
- catechol metabolite (`xmet:1500119`)
- dealkylated amine (`xmet:1500225`)
- dealkylated phenol (`xmet:1500226`)
- disulfide metabolite (`xmet:1500210`)
- ether glucuronide (`xmet:1500214`)
- glucuronide conjugate (`xmet:1500116`)
- glycine conjugate (`xmet:1500220`)
- hydroquinone metabolite (`xmet:1500200`)
- ketone metabolite (`xmet:1500229`)
- lactam metabolite (`xmet:1500211`)
- … +15 more direct children

## site type (`xmet:1600000`, ~72 descendants)

> Where on the molecule the transformation is localized.

- acyl attachment (`xmet:1600139`)
- alicyclic site (`xmet:1600200`)
- alkyl ether (`xmet:1600116`)
- alkyl halide (`xmet:1600127`)
- alkyne site (`xmet:1600210`)
- allylic carbon (`xmet:1600101`)
- allylic site (`xmet:1600015`)
- alpha to heteroatom (`xmet:1600017`)
- alpha to nitrogen (`xmet:1600140`)
- alpha to oxygen (`xmet:1600141`)
- alpha to sulfur (`xmet:1600142`)
- ambiguous site (`xmet:1600020`)
- amide (`xmet:1600122`)
- aniline (`xmet:1600103`)
- **aromatic site** (`xmet:1600013`)
  - fused benzene site (`xmet:1600201`)
- … +45 more direct children

## structural delta (`xmet:4000220`, ~86 descendants)

> Structural / formula / aromaticity / bond-order change facets.

- **aromatic and conjugated-system impact** (`xmet:8000000`)
  - arene oxide pathway (`xmet:8000007`): arene oxide rearrangement, NIH shift
  - aromatic ring substitution impact (`xmet:8000003`)
  - aromaticity gain (`xmet:8000002`): rearomatization
  - aromaticity loss (`xmet:8000001`): dearomatization
  - conjugated adduct formation (`xmet:8000008`)
  - conjugated π-system engagement (`xmet:8000004`)
  - heteroaromatic oxidation impact (`xmet:8000006`): thiophene epoxidation, thiophene S-oxidation
  - quinoid π-system formation (`xmet:8000005`)
- aromaticity change (`xmet:4000274`)
- aromaticity gain delta (`xmet:4000195`)
- aromaticity loss delta (`xmet:4000194`)
- atom added (`xmet:1700012`)
- atom removed (`xmet:1700013`)
- bond order change (`xmet:1700014`)
- bond order decrease (`xmet:1700110`)
- bond order increase (`xmet:1700109`)
- **bond-edit topology** (`xmet:7200000`)
  - atom addition (`xmet:7200001`)
  - bond cleavage (`xmet:7200002`)
  - bond order change (`xmet:7200003`)
  - bond-edit topology unspecified (`xmet:7200008`)
  - rearrangement topology (`xmet:7200005`)
  - ring closure (`xmet:4000405`)
  - ring opening topology (`xmet:7200007`)
  - substitution (`xmet:7200004`)
- charge change (`xmet:1700016`)
- conjugate moiety added (`xmet:1700018`)
- deethylation delta (`xmet:4000225`)
- demethylation delta (`xmet:4000224`)
- dioxygenation (`xmet:4000223`)
- … +15 more direct children

## product status (`xmet:1800000`, ~18 descendants)

> Observation / prediction / pathway status of a metabolite.

- artifact (`xmet:1800017`)
- authentic metabolite (`xmet:1800016`)
- circulating metabolite (`xmet:1800100`)
- excreted metabolite (`xmet:1800101`)
- intermediate metabolite (`xmet:1800012`)
- major metabolite (`xmet:1800015`)
- minor metabolite (`xmet:1800014`)
- not detected (`xmet:1800018`)
- observed product (`xmet:1800010`)
- predicted product (`xmet:1800011`)
- primary metabolite (`xmet:1800102`)
- putative metabolite (`xmet:1800105`)
- ruled out (`xmet:1800019`)
- secondary metabolite (`xmet:1800103`)
- structure elucidated (`xmet:1800106`)
- … +3 more direct children

## rule provenance (`xmet:1900000`, ~31 descendants)

> How a tag was produced (SMARTS, rule name, priority, exclusions).

- atom-map required match (`xmet:1900217`)
- caller CURIE match (`xmet:1900203`)
- caller-tag-derived (`xmet:1900012`)
- exclusion rule (`xmet:1900014`)
- exclusion SMARTS fired (`xmet:1900213`)
- Forest-map-derived tag (`xmet:1900013`)
- formula delta match (`xmet:1900202`)
- formula-delta-derived tag (`xmet:1900011`)
- harvest promotion (`xmet:1900216`)
- harvest-derived synonym (`xmet:1900103`)
- legacy model output (`xmet:1900102`)
- legacy reactivity model output (`xmet:1900212`)
- legacy SOM model output (`xmet:1900211`)
- manual curation (`xmet:1900104`)
- manual curator override (`xmet:1900215`)
- … +16 more direct children

## evidence (`xmet:2000000`, ~37 descendants)

> Evidence type supporting a named transformation or product.

- bile observation (`xmet:2000123`)
- chromatographic evidence (`xmet:2000110`)
- clinical evidence (`xmet:2000113`)
- conflicting evidence (`xmet:2000103`)
- curated assertion (`xmet:2000102`)
- exact-mass evidence (`xmet:2000107`)
- fragmentation evidence (`xmet:2000109`)
- hepatocyte evidence (`xmet:2000120`)
- hepatocyte incubation (`xmet:2000018`)
- high confidence assertion (`xmet:2000125`)
- HLM incubation (`xmet:2000017`)
- in vitro evidence (`xmet:2000111`)
- in vivo evidence (`xmet:2000112`)
- isotope pattern evidence (`xmet:2000108`)
- literature evidence (`xmet:2000010`)
- … +22 more direct children

## biological context (`xmet:2100000`, ~87 descendants)

> Orthogonal biological framing (enzyme, tissue, species, matrix).

- AO enzyme family context (`xmet:2100106`)
- **assay system** (`xmet:2100310`)
  - baculosome assay (`xmet:2100313`)
  - cytosol assay (`xmet:2100315`)
  - cytosol matrix context (`xmet:2100124`): cytosol assay
  - hepatocyte assay (`xmet:2100311`)
  - hepatocyte matrix context (`xmet:2100125`): hepatocyte assay
  - homogenate assay (`xmet:2100317`)
  - microsome assay (`xmet:2100312`)
  - microsome matrix context (`xmet:2100123`): microsome assay
  - … +6 more under assay system
- blood compartment (`xmet:2100129`)
- CES enzyme family context (`xmet:2100108`)
- CES1 context (`xmet:2100232`)
- CES2 context (`xmet:2100233`)
- compartment context (`xmet:2100014`)
- CYP enzyme family context (`xmet:2100100`)
- CYP1A2 context (`xmet:2100204`)
- CYP2C19 context (`xmet:2100203`)
- CYP2C9 context (`xmet:2100202`)
- CYP2D6 context (`xmet:2100201`)
- CYP2E1 context (`xmet:2100205`)
- CYP3A context (`xmet:2100200`)
- CYP3A4 context (`xmet:2100234`)
- … +31 more direct children

## ambiguity and underspecification (`xmet:6000000`, ~19 descendants)

> Cross-cutting spine for incomplete, conflicting, or underdetermined naming evidence. Prefer specific ambiguity subtypes; tag alongside positive terms rather than replacing them.

- **ambiguous reaction** (`xmet:6000001`)
  - aromatic-impact ambiguity (`xmet:6000060`)
  - electrophile-role ambiguity (`xmet:6000061`)
  - external-ontology alignment ambiguity (`xmet:6000052`)
  - forest-map correspondence ambiguity (`xmet:6000051`)
- aromatic-impact ambiguity (`xmet:6000060`)
- atom-mapping underspecification (`xmet:6000031`)
- competing-type ambiguity (`xmet:6000021`)
- electrophile-role ambiguity (`xmet:6000061`)
- external-ontology alignment ambiguity (`xmet:6000052`)
- forest-map correspondence ambiguity (`xmet:6000051`)
- formula-only evidence (`xmet:6000032`)
- fully specified (`xmet:6000099`)
- intermediate underspecification (`xmet:6000041`)
- mechanism ambiguity (`xmet:6000022`)
- **metabolite-structure underspecification** (`xmet:6000030`)
  - atom-mapping underspecification (`xmet:6000031`)
  - formula-only evidence (`xmet:6000032`)
- **pathway-depth ambiguity** (`xmet:6000040`)
  - intermediate underspecification (`xmet:6000041`)
- phase ambiguity (`xmet:6000050`)
- provenance underspecification (`xmet:6000070`)
- … +4 more direct children

## Metabolic Forest map (`xmet:9000000`, ~125 descendants)

> Alias / mapping spine for Metabolic Forest rulesets → rules → patterns. Opaque forest.* CURIEs only; not the chemist backbone.

- **bioactivation ruleset** (`xmet:9000019`)
  - NitroaromaticReduction rule (`xmet:9100511`)
- **conjugation ruleset** (`xmet:9000016`)
  - Acetylation rule (`xmet:9101020`)
  - Glucuronidation rule (`xmet:9101000`): Glucuronidation/alcohol, Glucuronidation/carboxylate
  - Glutathionation rule (`xmet:9101030`): Glutathionation/alkene, Glutathionation/aziridine_c, Glutathionation/aziridine_ch, Glutathionation/aziridine_ch2, Glutathionation/carbonyl, Glutathionation/epoxide_c, +7 more
  - Sulfation rule (`xmet:9101010`): Sulfation/alcohol, Sulfation/epoxide_methyl_sulfone
- **dehydrogenation ruleset** (`xmet:9000012`)
  - Dehydrogenation rule (`xmet:9100300`): Dehydrogenation/alcohol, Dehydrogenation/alkyl, Dehydrogenation/amine, Dehydrogenation/amine_end, Dehydrogenation/methide_end, Dehydrogenation/phenol_end, +1 more
- **hydrolysis ruleset** (`xmet:9000013`)
  - Hydrolysis rule (`xmet:9100400`): AzoSplitting rule, Dephosphorylation rule, EpoxideHydration rule, EpoxideOpening rule, Hydrolysis/add_water, Hydrolysis/cleave
- **phase I ruleset** (`xmet:9000018`)
  - dehydrogenation ruleset (`xmet:9000012`): Dehydrogenation rule
  - hydrolysis ruleset (`xmet:9000013`): Hydrolysis rule
  - reduction ruleset (`xmet:9000014`): Dehydration rule, Hydrogenation rule, NitrogenReduction rule, OxygenReduction rule, ReductiveDehalogenation rule, SulfurReduction rule
  - stable oxygenation ruleset (`xmet:9000010`): Epoxidation rule, Hydroxylation rule, NitrogenOxidation rule, SulfurOxidation rule
  - unstable oxygenation ruleset (`xmet:9000011`): Dealkylation rule, OxidativeDehalogenation rule
- **quinone formation ruleset** (`xmet:9000015`)
  - QuinoneFormation rule (`xmet:9100600`): QuinoneFormation/add_carbonyl_o, QuinoneFormation/dealkylate, QuinoneFormation/iminium, QuinoneFormation/replace_halogen, QuinoneFormation/single_to_double
- **reduction ruleset** (`xmet:9000014`)
  - Dehydration rule (`xmet:9100501`): Dehydration/alcohol, Dehydration/beta_elimination, Dehydration/carbonyl
  - Hydrogenation rule (`xmet:9100500`): Hydrogenation/alkene, Hydrogenation/alkyne, Hydrogenation/path_end
  - NitrogenReduction rule (`xmet:9100510`): BenzodioxoleReduction rule, NitroaromaticReduction rule, NitrogenReduction/hydroxylamine, NitrogenReduction/nitro_anion, NitrogenReduction/nitro_both, NitrogenReduction/nitro_both_any, +4 more
  - OxygenReduction rule (`xmet:9100520`): OxygenReduction/carbonyl, OxygenReduction/peroxide
  - ReductiveDehalogenation rule (`xmet:9100540`): ReductiveDehalogenation/alkene, ReductiveDehalogenation/cleave
  - SulfurReduction rule (`xmet:9100530`): SulfurReduction/disulfide, SulfurReduction/sulfoxide, SulfurReduction/thioether
- **stable oxygenation ruleset** (`xmet:9000010`)
  - Epoxidation rule (`xmet:9100110`): Epoxidation/epoxide
  - Hydroxylation rule (`xmet:9100100`): Hydroxylation/h, Hydroxylation/h2
  - NitrogenOxidation rule (`xmet:9100120`): NitrogenOxidation/hydroxylamine, NitrogenOxidation/n_oxide, NitrogenOxidation/nitroso
  - SulfurOxidation rule (`xmet:9100130`): SulfurOxidation/hydroxy, SulfurOxidation/oxo, SulfurOxidation/zwitterion, ThiopheneSulfurOxidation rule
- **tautomerization ruleset** (`xmet:9000017`)
  - Tautomerization rule (`xmet:9102000`)
- **unstable oxygenation ruleset** (`xmet:9000011`)
  - Dealkylation rule (`xmet:9100200`): Dealkylation/cc_alcohol, Dealkylation/cc_carbonyl, Dealkylation/cc_quaternary_alcohol, Dealkylation/hemiaminal, Dealkylation/methine_alcohol, Dealkylation/methine_carbonyl, +8 more
  - OxidativeDehalogenation rule (`xmet:9100210`): OxidativeDehalogenation/alcohol, OxidativeDehalogenation/carbonyl, OxidativeDehalogenation/carboxylic, OxidativeDehalogenation/gem_carboxylic, OxidativeDehalogenation/gem_hydrate, OxidativeDehalogenation/rearrange

## leaving group (`xmet:4000229`, ~30 descendants)

> Fragment or moiety that departs in a cleavage / substitution / dealkylation / hydrolysis step. Med-chem handle for soft-spot design.

- acetaldehyde leaving fragment (`xmet:4000251`)
- alcohol leaving fragment (`xmet:4000241`)
- allyl leaving group (`xmet:4000235`)
- amine leaving fragment (`xmet:4000242`)
- aryl leaving group (`xmet:4000253`)
- benzyl leaving group (`xmet:4000234`)
- bromide leaving group (`xmet:4000239`)
- carboxylate leaving group (`xmet:4000245`)
- chloride leaving group (`xmet:4000238`)
- cyanide leaving group (`xmet:4000257`)
- ethyl leaving group (`xmet:4000231`)
- fluoride leaving group (`xmet:4000237`)
- formaldehyde leaving fragment (`xmet:4000250`)
- halide leaving group (`xmet:4000236`)
- hydrogen leaving group (`xmet:4000249`)
- … +15 more direct children

## pharmacological role (`xmet:2300000`, ~10 descendants)

> Metabolism-specific pharmacological framing.

- active parent (`xmet:2300014`)
- equipotent metabolite (`xmet:2300016`)
- inactive parent (`xmet:2300015`)
- less active metabolite (`xmet:2300018`)
- more active metabolite (`xmet:2300017`)
- pharmacologically active metabolite (`xmet:2300010`)
- pharmacologically inactive metabolite (`xmet:2300011`)
- prodrug (`xmet:2300012`)
- prodrug activation (`xmet:1400127`)
- toxicophore-bearing metabolite (`xmet:2300019`)

## annotation about (`xmet:2400000`, ~6 descendants)

> Whether a tag is about parent, product, or reaction.

- about parent (`xmet:2400010`)
- about pathway (`xmet:2400015`)
- about product (`xmet:2400011`)
- about reaction (`xmet:2400012`)
- about site on parent (`xmet:2400013`)
- about site on product (`xmet:2400014`)

