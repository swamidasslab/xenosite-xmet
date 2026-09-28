# Draft: reaction class — Phase I (when + pair + tagger rules)

Status: **discussion draft** — not applied to `xmet.yaml`.

Parseable twin: [`draft-reaction-class-phase1-tree.json`](draft-reaction-class-phase1-tree.json).

Sources: Forest PhaseOneRS PatternInfo (`when`, pair endpoints) **and** tagger rules in
`crates/xenosite-tagger/data/rules/{xenobiotic,structural}.rules.yaml`.

Tagger: 329 non-delta rules scanned; 124 attachments onto Phase I Forest rules.

## reaction class

### Stable Oxygenation

- ↔ `forest.ruleset:SO`

#### N-oxidation  `[single]`

- ↔ `forest.rule:NitrogenOxidation`

- **tagger rules (9):** `rule:forest-tag-nitrogenoxidation_hydroxylamine`, `rule:forest-tag-nitrogenreduction_hydroxylamine`, `rule:struct-n-oxidation`, `rule:struct-hydroxylamine-formation`, `rule:struct-carbon-oxidation`, `rule:struct-n-oxide-reduction`, `rule:struct-nitroso-formation`, `rule:struct-aromatic-amine-n-oxidation`, `rule:struct-primary-amine-n-oxidation`

- **hydroxylamine** (pattern) ↔ `forest.pattern:NitrogenOxidation/hydroxylamine`

  - `when`: `[{"map": 1, "z": 7, "h": 1}, {"map": 1, "z": 7, "h": 2}]` partners=[]

  - *from when:* N-centered

  - *specialize:* forest nitrogenoxidation_hydroxylamine

  - *specialize:* forest nitrogenreduction_hydroxylamine

  - *specialize:* hydroxylamine formation

  - *tagger:* `rule:forest-tag-nitrogenoxidation_hydroxylamine` → None

  - *tagger:* `rule:forest-tag-nitrogenreduction_hydroxylamine` → None

  - *tagger:* `rule:struct-hydroxylamine-formation` → xmet:0000122

- **nitroso** (pattern) ↔ `forest.pattern:NitrogenOxidation/nitroso`

- **n oxide** (pattern) ↔ `forest.pattern:NitrogenOxidation/n_oxide`

  - *specialize:* n oxide reduction

  - *tagger:* `rule:struct-n-oxide-reduction` → xmet:0000515


#### S-oxidation  `[single]`

- ↔ `forest.rule:SulfurOxidation`

- **tagger rules (7):** `rule:forest-tag-dehydrogenation_sulfoxide`, `rule:forest-tag-sulfation_epoxide_methyl_sulfone`, `rule:forest-tag-sulfurreduction_sulfoxide`, `rule:struct-s-oxidation`, `rule:struct-thiophene-s-oxidation`, `rule:struct-sulfone-formation`, `rule:struct-sulfoxide-reduction`

- *extend:* thiophene S-oxidation — forest.rule:ThiopheneSulfurOxidation

- **zwitterion** (pattern) ↔ `forest.pattern:SulfurOxidation/zwitterion`

- **hydroxy** (pattern) ↔ `forest.pattern:SulfurOxidation/hydroxy`

- **oxo** (pattern) ↔ `forest.pattern:SulfurOxidation/oxo`


#### epoxidation  `[resonance]`

- ↔ `forest.rule:Epoxidation`

- **tagger rules (9):** `rule:epoxidation`, `rule:tag-epoxidation`, `rule:tag-arene-oxide`, `rule:tag-nih-shift`, `rule:tag-ipso`, `rule:struct-epoxidation`, `rule:struct-alkene-epoxidation`, `rule:struct-aromatic-epoxidation`, `rule:struct-arene-oxide-formation`

- *extend:* arene oxide formation — named aromatic epoxidation path

- **epoxide** (pattern) ↔ `forest.pattern:Epoxidation/epoxide`

  - `when`: `[{"map": 2, "z": 6}, {"map": 2, "z": 7}]` partners=['C', 'N']

  - *from when:* N-centered

  - *from when:* partner C

  - *from when:* partner N

  - *specialize:* aromatic epoxidation

  - *specialize:* aliphatic / alkene epoxidation

  - *specialize:* arene oxide

  - *specialize:* nih shift

  - *specialize:* ipso

  - *specialize:* alkene epoxidation

  - *specialize:* arene oxide formation

  - *tagger:* `rule:tag-arene-oxide` → xmet:0000112

  - *tagger:* `rule:tag-nih-shift` → xmet:0004003

  - *tagger:* `rule:tag-ipso` → xmet:0004004

  - *tagger:* `rule:struct-alkene-epoxidation` → xmet:0000111

  - *tagger:* `rule:struct-aromatic-epoxidation` → xmet:0000110

  - *tagger:* `rule:struct-arene-oxide-formation` → xmet:0000112


#### hydroxylation  `[single]`

- ↔ `forest.rule:Hydroxylation`

- **tagger rules (17):** `rule:hydroxylation`, `rule:aromatic-hydroxylation`, `rule:aliphatic-hydroxylation`, `rule:tag-hydroxylation`, `rule:tag-aromatic-hydroxylation`, `rule:tag-para-hydroxylation`, `rule:tag-benzylic-hydroxylation`, `rule:tag-omega-hydroxylation`, `rule:struct-hydroxylation`, `rule:struct-aromatic-hydroxylation`, `rule:struct-aliphatic-hydroxylation`, `rule:struct-allylic-hydroxylation`, `rule:struct-benzylic-hydroxylation`, `rule:struct-ortho-hydroxylation`, `rule:struct-para-hydroxylation`, `rule:struct-meta-hydroxylation`, `rule:struct-omega-1-hydroxylation`

- **h** (pattern) ↔ `forest.pattern:Hydroxylation/h`

  - `when`: `[{"map": 1, "z": 6, "h": 1}]` partners=[]

  - *from when:* methine CH

  - *specialize:* aromatic hydroxylation

  - *specialize:* aliphatic hydroxylation

  - *specialize:* benzylic hydroxylation

  - *specialize:* allylic hydroxylation

  - *specialize:* para hydroxylation

  - *specialize:* ortho hydroxylation

  - *specialize:* meta hydroxylation

  - *tagger:* `rule:aromatic-hydroxylation` → xmet:0000101

  - *tagger:* `rule:tag-aromatic-hydroxylation` → xmet:0000101

  - *tagger:* `rule:tag-para-hydroxylation` → xmet:0000103

  - *tagger:* `rule:struct-aromatic-hydroxylation` → xmet:0000101

  - *tagger:* `rule:struct-ortho-hydroxylation` → xmet:0000104

  - *tagger:* `rule:struct-para-hydroxylation` → xmet:0000103

  - *tagger:* `rule:struct-meta-hydroxylation` → xmet:0000105

- **h2** (pattern) ↔ `forest.pattern:Hydroxylation/h2`

  - `when`: `[{"map": 1, "z": 6, "h": 2}, {"map": 1, "z": 6, "h": 3}]` partners=[]

  - *from when:* methylene CH2

  - *from when:* methyl CH3

  - *specialize:* omega hydroxylation

  - *specialize:* omega-1 hydroxylation

  - *specialize:* aliphatic hydroxylation

  - *specialize:* benzylic hydroxylation

  - *specialize:* allylic hydroxylation

  - *specialize:* omega 1 hydroxylation

  - *tagger:* `rule:aliphatic-hydroxylation` → xmet:0000102

  - *tagger:* `rule:tag-benzylic-hydroxylation` → xmet:0000106

  - *tagger:* `rule:tag-omega-hydroxylation` → xmet:0000108

  - *tagger:* `rule:struct-aliphatic-hydroxylation` → xmet:0000102

  - *tagger:* `rule:struct-allylic-hydroxylation` → xmet:0000107

  - *tagger:* `rule:struct-benzylic-hydroxylation` → xmet:0000106

  - *tagger:* `rule:struct-omega-1-hydroxylation` → xmet:0000109


### Unstable Oxygenation

- ↔ `forest.ruleset:UO`

#### dealkylation  `[resonance]`

- ↔ `forest.rule:Dealkylation`

- **tagger rules (19):** `rule:tag-dealkylation`, `rule:tag-n-dealkylation`, `rule:tag-n-demethylation`, `rule:tag-oxidative-deamination`, `rule:tag-o-dealkylation`, `rule:tag-o-demethylation`, `rule:struct-n-demethylation`, `rule:struct-o-dealkylation`, `rule:struct-n-dealkylation`, `rule:struct-n-dealkylation-secondary`, `rule:struct-n-deethylation`, `rule:struct-n-depropylation`, `rule:struct-o-deethylation`, `rule:struct-aromatic-o-dealkylation`, `rule:struct-s-dealkylation`, `rule:struct-c-dealkylation`, `rule:struct-dearylation`, `rule:struct-dealkylation`, `rule:struct-aliphatic-o-dealkylation`

- **methyl carboxylic** (pattern) ↔ `forest.pattern:Dealkylation/methyl_carboxylic`

  - `when`: `[{"map": 2, "z": 7}, {"map": 2, "z": 8}, {"map": 2, "z": 16}]` partners=['N', 'O', 'S']

  - *from when:* N-centered

  - *from when:* O-centered

  - *from when:* S-centered

  - *from when:* partner N

  - *from when:* N-dealkylation

  - *from when:* partner O

  - *from when:* O-dealkylation

  - *from when:* partner S

  - *from when:* S-dealkylation

- **methyl carbonyl** (pattern) ↔ `forest.pattern:Dealkylation/methyl_carbonyl`

  - `when`: `[{"map": 2, "z": 7}, {"map": 2, "z": 8}, {"map": 2, "z": 16}]` partners=['N', 'O', 'S']

  - *from when:* N-centered

  - *from when:* O-centered

  - *from when:* S-centered

  - *from when:* partner N

  - *from when:* N-dealkylation

  - *from when:* partner O

  - *from when:* O-dealkylation

  - *from when:* partner S

  - *from when:* S-dealkylation

- **methyl alcohol** (pattern) ↔ `forest.pattern:Dealkylation/methyl_alcohol`

  - `when`: `[{"map": 2, "z": 7}, {"map": 2, "z": 8}, {"map": 2, "z": 16}]` partners=['N', 'O', 'S']

  - *from when:* N-centered

  - *from when:* O-centered

  - *from when:* S-centered

  - *from when:* partner N

  - *from when:* N-dealkylation

  - *from when:* partner O

  - *from when:* O-dealkylation

  - *from when:* partner S

  - *from when:* S-dealkylation

  - *specialize:* n demethylation

  - *tagger:* `rule:tag-n-demethylation` → xmet:0000205

  - *tagger:* `rule:struct-n-demethylation` → xmet:0000205

- **methylene carboxylic** (pattern) ↔ `forest.pattern:Dealkylation/methylene_carboxylic`

  - `when`: `[{"map": 2, "z": 7}, {"map": 2, "z": 8}, {"map": 2, "z": 16}]` partners=['N', 'O', 'S']

  - *from when:* N-centered

  - *from when:* O-centered

  - *from when:* S-centered

  - *from when:* partner N

  - *from when:* N-dealkylation

  - *from when:* partner O

  - *from when:* O-dealkylation

  - *from when:* partner S

  - *from when:* S-dealkylation

- **methylene carbonyl** (pattern) ↔ `forest.pattern:Dealkylation/methylene_carbonyl`

  - `when`: `[{"map": 2, "z": 7}, {"map": 2, "z": 8}, {"map": 2, "z": 16}]` partners=['N', 'O', 'S']

  - *from when:* N-centered

  - *from when:* O-centered

  - *from when:* S-centered

  - *from when:* partner N

  - *from when:* N-dealkylation

  - *from when:* partner O

  - *from when:* O-dealkylation

  - *from when:* partner S

  - *from when:* S-dealkylation

- **methylene alcohol** (pattern) ↔ `forest.pattern:Dealkylation/methylene_alcohol`

  - `when`: `[{"map": 2, "z": 7}, {"map": 2, "z": 8}, {"map": 2, "z": 16}]` partners=['N', 'O', 'S']

  - *from when:* N-centered

  - *from when:* O-centered

  - *from when:* S-centered

  - *from when:* partner N

  - *from when:* N-dealkylation

  - *from when:* partner O

  - *from when:* O-dealkylation

  - *from when:* partner S

  - *from when:* S-dealkylation

  - *specialize:* n deethylation

  - *specialize:* n depropylation

  - *tagger:* `rule:struct-n-deethylation` → xmet:0000206

  - *tagger:* `rule:struct-n-depropylation` → xmet:0000207

- **methine carbonyl** (pattern) ↔ `forest.pattern:Dealkylation/methine_carbonyl`

  - `when`: `[{"map": 2, "z": 7}, {"map": 2, "z": 8}, {"map": 2, "z": 16}]` partners=['N', 'O', 'S']

  - *from when:* N-centered

  - *from when:* O-centered

  - *from when:* S-centered

  - *from when:* partner N

  - *from when:* N-dealkylation

  - *from when:* partner O

  - *from when:* O-dealkylation

  - *from when:* partner S

  - *from when:* S-dealkylation

- **methine alcohol** (pattern) ↔ `forest.pattern:Dealkylation/methine_alcohol`

  - `when`: `[{"map": 2, "z": 7}, {"map": 2, "z": 8}, {"map": 2, "z": 16}]` partners=['N', 'O', 'S']

  - *from when:* N-centered

  - *from when:* O-centered

  - *from when:* S-centered

  - *from when:* partner N

  - *from when:* N-dealkylation

  - *from when:* partner O

  - *from when:* O-dealkylation

  - *from when:* partner S

  - *from when:* S-dealkylation

- **quaternary alcohol** (pattern) ↔ `forest.pattern:Dealkylation/quaternary_alcohol`

  - `when`: `[{"map": 2, "z": 7}, {"map": 2, "z": 8}, {"map": 2, "z": 16}]` partners=['N', 'O', 'S']

  - *from when:* N-centered

  - *from when:* O-centered

  - *from when:* S-centered

  - *from when:* partner N

  - *from when:* N-dealkylation

  - *from when:* partner O

  - *from when:* O-dealkylation

  - *from when:* partner S

  - *from when:* S-dealkylation

- **cc quaternary alcohol** (pattern) ↔ `forest.pattern:Dealkylation/cc_quaternary_alcohol`

  - `when`: `[]` partners=['C']

  - *from when:* partner C

  - *from when:* C-dealkylation

- **cc alcohol** (pattern) ↔ `forest.pattern:Dealkylation/cc_alcohol`

  - `when`: `[{"map": 1, "z": 6, "h": 1}, {"map": 1, "z": 6, "h": 2}, {"map": 1, "z": 6, "h": 3}]` partners=['C']

  - *from when:* methine CH

  - *from when:* methylene CH2

  - *from when:* methyl CH3

  - *from when:* partner C

  - *from when:* C-dealkylation

  - *specialize:* c dealkylation

  - *specialize:* dearylation

  - *tagger:* `rule:struct-c-dealkylation` → xmet:0000204

  - *tagger:* `rule:struct-dearylation` → xmet:0000720

- **cc carbonyl** (pattern) ↔ `forest.pattern:Dealkylation/cc_carbonyl`

  - `when`: `[{"map": 1, "z": 6, "h": 1}, {"map": 1, "z": 6, "h": 2}, {"map": 1, "z": 6, "h": 3}]` partners=['C']

  - *from when:* methine CH

  - *from when:* methylene CH2

  - *from when:* methyl CH3

  - *from when:* partner C

  - *from when:* C-dealkylation

- **hemiaminal** (pattern) ↔ `forest.pattern:Dealkylation/hemiaminal`

  - `when`: `[{"map": 2, "z": 7}, {"map": 2, "z": 8}, {"map": 2, "z": 16}]` partners=['N', 'O', 'S']

  - *from when:* N-centered

  - *from when:* O-centered

  - *from when:* S-centered

  - *from when:* partner N

  - *from when:* N-dealkylation

  - *from when:* partner O

  - *from when:* O-dealkylation

  - *from when:* partner S

  - *from when:* S-dealkylation

  - *specialize:* oxidative deamination


#### oxidative dehalogenation  `[single]`

- ↔ `forest.rule:OxidativeDehalogenation`

- **tagger rules (4):** `rule:struct-oxidative-dehalogenation`, `rule:struct-oxidative-defluorination`, `rule:struct-oxidative-dechlorination`, `rule:struct-oxidative-debromination`

- **alcohol** (pattern) ↔ `forest.pattern:OxidativeDehalogenation/alcohol`

  - `when`: `[{"map": 1, "z": 9}, {"map": 1, "z": 17}, {"map": 1, "z": 35}, {"map": 1, "z": 53}, {"map": 1, "z": 85}]` partners=['At', 'Br', 'Cl', 'F', 'I']

  - *from when:* halogen F

  - *from when:* halogen Cl

  - *from when:* halogen Br

  - *from when:* halogen I

  - *from when:* halogen At

  - *from when:* partner At

  - *from when:* partner Br

  - *from when:* partner Cl

  - *from when:* partner F

  - *from when:* partner I

  - *from when:* oxidative defluorination

  - *from when:* oxidative dechlorination

  - *from when:* oxidative debromination

  - *from when:* oxidative deiodination

- **carbonyl** (pattern) ↔ `forest.pattern:OxidativeDehalogenation/carbonyl`

  - `when`: `[{"map": 1, "z": 9}, {"map": 1, "z": 17}, {"map": 1, "z": 35}, {"map": 1, "z": 53}, {"map": 1, "z": 85}]` partners=['At', 'Br', 'Cl', 'F', 'I']

  - *from when:* halogen F

  - *from when:* halogen Cl

  - *from when:* halogen Br

  - *from when:* halogen I

  - *from when:* halogen At

  - *from when:* partner At

  - *from when:* partner Br

  - *from when:* partner Cl

  - *from when:* partner F

  - *from when:* partner I

  - *from when:* oxidative defluorination

  - *from when:* oxidative dechlorination

  - *from when:* oxidative debromination

  - *from when:* oxidative deiodination

- **carboxylic** (pattern) ↔ `forest.pattern:OxidativeDehalogenation/carboxylic`

  - `when`: `[{"map": 1, "z": 9}, {"map": 1, "z": 17}, {"map": 1, "z": 35}, {"map": 1, "z": 53}, {"map": 1, "z": 85}]` partners=['At', 'Br', 'Cl', 'F', 'I']

  - *from when:* halogen F

  - *from when:* halogen Cl

  - *from when:* halogen Br

  - *from when:* halogen I

  - *from when:* halogen At

  - *from when:* partner At

  - *from when:* partner Br

  - *from when:* partner Cl

  - *from when:* partner F

  - *from when:* partner I

  - *from when:* oxidative defluorination

  - *from when:* oxidative dechlorination

  - *from when:* oxidative debromination

  - *from when:* oxidative deiodination

- **rearrange** (pattern) ↔ `forest.pattern:OxidativeDehalogenation/rearrange`

  - `when`: `[{"map": 1, "z": 9}, {"map": 1, "z": 17}, {"map": 1, "z": 35}, {"map": 1, "z": 53}, {"map": 1, "z": 85}]` partners=['At', 'Br', 'Cl', 'F', 'I']

  - *from when:* halogen F

  - *from when:* halogen Cl

  - *from when:* halogen Br

  - *from when:* halogen I

  - *from when:* halogen At

  - *from when:* partner At

  - *from when:* partner Br

  - *from when:* partner Cl

  - *from when:* partner F

  - *from when:* partner I

  - *from when:* oxidative defluorination

  - *from when:* oxidative dechlorination

  - *from when:* oxidative debromination

  - *from when:* oxidative deiodination

- **gem carboxylic** (pattern) ↔ `forest.pattern:OxidativeDehalogenation/gem_carboxylic`

  - `when`: `[{"map": 1, "z": 9}, {"map": 1, "z": 17}, {"map": 1, "z": 35}, {"map": 1, "z": 53}, {"map": 1, "z": 85}]` partners=['At', 'Br', 'Cl', 'F', 'I']

  - *from when:* halogen F

  - *from when:* halogen Cl

  - *from when:* halogen Br

  - *from when:* halogen I

  - *from when:* halogen At

  - *from when:* partner At

  - *from when:* partner Br

  - *from when:* partner Cl

  - *from when:* partner F

  - *from when:* partner I

  - *from when:* oxidative defluorination

  - *from when:* oxidative dechlorination

  - *from when:* oxidative debromination

  - *from when:* oxidative deiodination

- **gem hydrate** (pattern) ↔ `forest.pattern:OxidativeDehalogenation/gem_hydrate`

  - `when`: `[{"map": 1, "z": 9}, {"map": 1, "z": 17}, {"map": 1, "z": 35}, {"map": 1, "z": 53}, {"map": 1, "z": 85}]` partners=['At', 'Br', 'Cl', 'F', 'I']

  - *from when:* halogen F

  - *from when:* halogen Cl

  - *from when:* halogen Br

  - *from when:* halogen I

  - *from when:* halogen At

  - *from when:* partner At

  - *from when:* partner Br

  - *from when:* partner Cl

  - *from when:* partner F

  - *from when:* partner I

  - *from when:* oxidative defluorination

  - *from when:* oxidative dechlorination

  - *from when:* oxidative debromination

  - *from when:* oxidative deiodination


### Dehydrogenation

- ↔ `forest.ruleset:DH`

- *extend:* quinone formation (Rainbow DH link) — composites primary; curated DH link

#### dehydrogenation  `[pair]`

- ↔ `forest.rule:Dehydrogenation`

- _ResonancePair / atom_pair rule: one emission matches TWO endpoint patterns (see pair_combinations). Same swap_group → unordered; different → ordered._

- **tagger rules (21):** `rule:alcohol-oxidation`, `rule:primary-alcohol-oxidation`, `rule:tag-dearomatization`, `rule:tag-quinone-imine`, `rule:tag-imine-methide`, `rule:forest-tag-dehydrogenation_alcohol`, `rule:forest-tag-dehydrogenation_alkyl`, `rule:forest-tag-dehydrogenation_amine`, `rule:forest-tag-dehydrogenation_amine_end`, `rule:forest-tag-dehydrogenation_methide_end`, `rule:forest-tag-dehydrogenation_phenol_end`, `rule:forest-tag-quinoneformation_iminium`, `rule:forest-tag-dehydrogenation`, `rule:struct-alcohol-oxidation`, `rule:struct-aromatization`, `rule:struct-alkene-formation`, `rule:struct-primary-alcohol-oxidation`, `rule:struct-secondary-alcohol-oxidation`, `rule:struct-double-to-triple-dehydrogenation`, `rule:struct-imine-enamine-tautomerization` …

- *extend:* aromatization — named DH path

- **sulfoxide** (pattern) ↔ `forest.pattern:Dehydrogenation/sulfoxide`

- **alcohol** (pattern) ↔ `forest.pattern:Dehydrogenation/alcohol`

  - `when`: `[]` partners=['O']

  - *from when:* partner O

  - *specialize:* primary alcohol → aldehyde

  - *specialize:* secondary alcohol → ketone

  - *specialize:* alcohol oxidation

  - *specialize:* primary alcohol oxidation

  - *specialize:* secondary alcohol oxidation

  - *tagger:* `rule:alcohol-oxidation` → xmet:0000310

  - *tagger:* `rule:primary-alcohol-oxidation` → xmet:0000311

  - *tagger:* `rule:struct-alcohol-oxidation` → xmet:0000310

  - *tagger:* `rule:struct-primary-alcohol-oxidation` → xmet:0000311

  - *tagger:* `rule:struct-secondary-alcohol-oxidation` → xmet:0000312

- **amine** (pattern) ↔ `forest.pattern:Dehydrogenation/amine`

  - `when`: `[{"map": 2, "z": 7, "h": 2}, {"map": 2, "z": 7, "h": 1}]` partners=['N']

  - *from when:* N-centered

  - *from when:* partner N

  - *specialize:* imine formation

  - *specialize:* iminium ion formation

  - *specialize:* quinone imine

  - *specialize:* imine methide

  - *specialize:* forest quinoneformation_iminium

  - *specialize:* imine enamine tautomerization

  - *specialize:* iminium formation

  - *tagger:* `rule:tag-quinone-imine` → xmet:0000303

  - *tagger:* `rule:tag-imine-methide` → xmet:0000306

  - *tagger:* `rule:forest-tag-quinoneformation_iminium` → None

  - *tagger:* `rule:struct-imine-enamine-tautomerization` → xmet:0002002

  - *tagger:* `rule:struct-iminium-formation` → xmet:0000305

- **alkyl** (pattern) ↔ `forest.pattern:Dehydrogenation/alkyl`

  - `when`: `[{"map": 2, "z": 6, "h": 3}, {"map": 2, "z": 6, "h": 2}, {"map": 2, "z": 6, "h": 1}]` partners=['C']

  - *from when:* methyl CH3

  - *from when:* methylene CH2

  - *from when:* methine CH

  - *from when:* partner C

- **phenol end** (endpoint) ↔ `forest.pattern:Dehydrogenation/phenol_end`

  - `when`: `[]` partners=['O']

  - *from when:* partner O

- **amine end** (endpoint) ↔ `forest.pattern:Dehydrogenation/amine_end`

  - `when`: `[{"map": 2, "z": 7, "h": 2}, {"map": 2, "z": 7, "h": 1}]` partners=[]

  - *from when:* N-centered

- **methide end** (endpoint) ↔ `forest.pattern:Dehydrogenation/methide_end`

  - `when`: `[{"map": 2, "z": 6, "h": 3}, {"map": 2, "z": 6, "h": 2}, {"map": 2, "z": 6, "h": 1}]` partners=['C']

  - *from when:* methyl CH3

  - *from when:* methylene CH2

  - *from when:* methine CH

  - *from when:* partner C

- **pair combinations:**

  - *pair (unordered):* phenol end × phenol end

  - *pair (ordered):* phenol end × amine end

  - *pair (ordered):* amine end × phenol end

  - *pair (ordered):* phenol end × methide end

  - *pair (ordered):* methide end × phenol end

  - *pair (unordered):* amine end × amine end

  - *pair (ordered):* amine end × methide end

  - *pair (ordered):* methide end × amine end

  - *pair (unordered):* methide end × methide end


### Hydrolysis

- ↔ `forest.ruleset:HD`

- *extend:* azo cleavage — Forest Full HD / AzoSplitting

#### dephosphorylation  `[single]`

- ↔ `forest.rule:Dephosphorylation`

- **tagger rules (3):** `rule:forest-tag-dephosphorylation_phosphate_ester`, `rule:forest-tag-dephosphorylation`, `rule:struct-dephosphorylation`

- **phosphate ester** (pattern) ↔ `forest.pattern:Dephosphorylation/phosphate_ester`

  - `when`: `[{"map": 2, "z": 15}]` partners=['P']

  - *from when:* P-centered

  - *from when:* partner P


#### epoxide opening  `[single]`

- ↔ `forest.rule:EpoxideOpening`

- **tagger rules (1):** `rule:struct-epoxide-opening`

- **rearrange** (pattern) ↔ `forest.pattern:EpoxideOpening/rearrange`

- **hydrate** (pattern) ↔ `forest.pattern:EpoxideOpening/hydrate`


#### hydrolysis  `[single]`

- ↔ `forest.rule:Hydrolysis`

- **tagger rules (9):** `rule:tag-ether-hydrolysis`, `rule:struct-ester-hydrolysis`, `rule:struct-hydrolysis`, `rule:struct-lactamization`, `rule:struct-amide-hydrolysis`, `rule:struct-lactam-hydrolysis`, `rule:struct-carbamate-hydrolysis`, `rule:struct-nitrile-hydrolysis`, `rule:struct-ether-hydrolysis`

- **add water** (pattern) ↔ `forest.pattern:Hydrolysis/add_water`

  - `when`: `[{"map": 3, "z": 7}, {"map": 3, "z": 8}, {"map": 3, "z": 16}]` partners=['N', 'O', 'S']

  - *from when:* N-centered

  - *from when:* O-centered

  - *from when:* S-centered

  - *from when:* partner N

  - *from when:* partner O

  - *from when:* partner S

- **cleave** (pattern) ↔ `forest.pattern:Hydrolysis/cleave`

  - `when`: `[{"map": 3, "z": 7}, {"map": 3, "z": 8}, {"map": 3, "z": 16}]` partners=['N', 'O', 'S']

  - *from when:* N-centered

  - *from when:* O-centered

  - *from when:* S-centered

  - *from when:* partner N

  - *from when:* partner O

  - *from when:* partner S

  - *specialize:* ester hydrolysis

  - *specialize:* amide hydrolysis

  - *specialize:* carbamate hydrolysis

  - *specialize:* ether hydrolysis

  - *specialize:* nitrile hydrolysis

  - *specialize:* lactamization

  - *specialize:* lactam hydrolysis

  - *tagger:* `rule:tag-ether-hydrolysis` → xmet:0000408

  - *tagger:* `rule:struct-ester-hydrolysis` → xmet:0000401

  - *tagger:* `rule:struct-lactamization` → xmet:0000633

  - *tagger:* `rule:struct-amide-hydrolysis` → xmet:0000402

  - *tagger:* `rule:struct-lactam-hydrolysis` → xmet:0000404

  - *tagger:* `rule:struct-carbamate-hydrolysis` → xmet:0000405

  - *tagger:* `rule:struct-nitrile-hydrolysis` → xmet:0000411

  - *tagger:* `rule:struct-ether-hydrolysis` → xmet:0000408


### Reduction

- ↔ `forest.ruleset:RD`

- *extend:* benzodioxole reduction — Forest Full RD / BenzodioxoleReduction

#### dehydration  `[single]`

- ↔ `forest.rule:Dehydration`

- **tagger rules (6):** `rule:forest-tag-dehydration_alcohol`, `rule:forest-tag-dehydration_beta_elimination`, `rule:forest-tag-dehydration_carbonyl`, `rule:forest-tag-epoxidehydration_diol`, `rule:forest-tag-dehydration`, `rule:forest-tag-epoxidehydration`

- **alcohol** (pattern) ↔ `forest.pattern:Dehydration/alcohol`

  - `when`: `[{"map": 1, "z": 6}, {"map": 1, "z": 7}]` partners=['O']

  - *from when:* N-centered

  - *from when:* partner O

- **beta elimination** (pattern) ↔ `forest.pattern:Dehydration/beta_elimination`

  - `when`: `[]` partners=['O']

  - *from when:* partner O

- **carbonyl** (pattern) ↔ `forest.pattern:Dehydration/carbonyl`

  - `when`: `[{"map": 1, "z": 6}, {"map": 1, "z": 7}]` partners=['O']

  - *from when:* N-centered

  - *from when:* partner O


#### hydrogenation  `[pair]`

- ↔ `forest.rule:Hydrogenation`

- _ResonancePair / atom_pair rule: one emission matches TWO endpoint patterns (see pair_combinations). Same swap_group → unordered; different → ordered._

- **tagger rules (6):** `rule:forest-tag-hydrogenation_alkene`, `rule:forest-tag-hydrogenation_alkyne`, `rule:forest-tag-hydrogenation_path_end`, `rule:forest-tag-hydrogenation`, `rule:struct-hydrogenation`, `rule:struct-alkyne-hydrogenation`

- **alkyne** (pattern) ↔ `forest.pattern:Hydrogenation/alkyne`

- **alkene** (pattern) ↔ `forest.pattern:Hydrogenation/alkene`

- **path end** (endpoint) ↔ `forest.pattern:Hydrogenation/path_end`

- **pair combinations:**

  - *pair (unordered):* path end × path end


#### nitrogen reduction  `[resonance]`

- ↔ `forest.rule:NitrogenReduction`

- **tagger rules (4):** `rule:tag-nitro-reduction`, `rule:tag-nitroaromatic-reduction`, `rule:struct-nitrogen-reduction`, `rule:struct-nitro-reduction`

- *extend:* nitroaromatic reduction — forest.rule:NitroaromaticReduction

- **nitro charged** (pattern) ↔ `forest.pattern:NitrogenReduction/nitro_charged`

  - `when`: `[]` partners=['O']

  - *from when:* partner O

- **nitro anion** (pattern) ↔ `forest.pattern:NitrogenReduction/nitro_anion`

  - `when`: `[]` partners=['O']

  - *from when:* partner O

- **nitro neutral** (pattern) ↔ `forest.pattern:NitrogenReduction/nitro_neutral`

  - `when`: `[]` partners=['O']

  - *from when:* partner O

- **nitro to amine** (pattern) ↔ `forest.pattern:NitrogenReduction/nitro_to_amine`

  - `when`: `[]` partners=['O']

  - *from when:* partner O

- **nitro both** (pattern) ↔ `forest.pattern:NitrogenReduction/nitro_both`

  - `when`: `[]` partners=['O']

  - *from when:* partner O

- **hydroxylamine** (pattern) ↔ `forest.pattern:NitrogenReduction/hydroxylamine`

  - `when`: `[]` partners=['O']

  - *from when:* partner O

- **nitroso** (pattern) ↔ `forest.pattern:NitrogenReduction/nitroso`

  - `when`: `[]` partners=['O']

  - *from when:* partner O

- **nitro both any** (pattern) ↔ `forest.pattern:NitrogenReduction/nitro_both_any`

  - `when`: `[]` partners=['O']

  - *from when:* partner O


#### oxygen reduction  `[single]`

- ↔ `forest.rule:OxygenReduction`

- **tagger rules (3):** `rule:tag-carbonyl-reduction`, `rule:struct-aldehyde-reduction`, `rule:struct-ketone-reduction`

- **carbonyl** (pattern) ↔ `forest.pattern:OxygenReduction/carbonyl`

  - `when`: `[{"map": 2, "z": 6}, {"map": 2, "z": 7}]` partners=['C', 'N']

  - *from when:* N-centered

  - *from when:* partner C

  - *from when:* partner N

  - *specialize:* carbonyl reduction

  - *specialize:* aldehyde reduction

  - *specialize:* ketone reduction

  - *tagger:* `rule:tag-carbonyl-reduction` → xmet:0000524

  - *tagger:* `rule:struct-aldehyde-reduction` → xmet:0000522

  - *tagger:* `rule:struct-ketone-reduction` → xmet:0000521

- **peroxide** (pattern) ↔ `forest.pattern:OxygenReduction/peroxide`

  - `when`: `[]` partners=['O']

  - *from when:* partner O


#### reductive dehalogenation  `[single]`

- ↔ `forest.rule:ReductiveDehalogenation`

- **tagger rules (2):** `rule:struct-reductive-dehalogenation`, `rule:struct-reductive-dechlorination`

- **cleave** (pattern) ↔ `forest.pattern:ReductiveDehalogenation/cleave`

  - `when`: `[{"map": 1, "z": 9}, {"map": 1, "z": 17}, {"map": 1, "z": 35}, {"map": 1, "z": 53}, {"map": 1, "z": 85}]` partners=['At', 'Br', 'Cl', 'F', 'I']

  - *from when:* halogen F

  - *from when:* halogen Cl

  - *from when:* halogen Br

  - *from when:* halogen I

  - *from when:* halogen At

  - *from when:* partner At

  - *from when:* partner Br

  - *from when:* partner Cl

  - *from when:* partner F

  - *from when:* partner I

  - *from when:* reductive defluorination

  - *from when:* reductive dechlorination

  - *from when:* reductive debromination

  - *from when:* reductive deiodination

- **alkene** (pattern) ↔ `forest.pattern:ReductiveDehalogenation/alkene`

  - `when`: `[{"map": 1, "z": 9}, {"map": 1, "z": 17}, {"map": 1, "z": 35}, {"map": 1, "z": 53}, {"map": 1, "z": 85}]` partners=['At', 'Br', 'Cl', 'F', 'I']

  - *from when:* halogen F

  - *from when:* halogen Cl

  - *from when:* halogen Br

  - *from when:* halogen I

  - *from when:* halogen At

  - *from when:* partner At

  - *from when:* partner Br

  - *from when:* partner Cl

  - *from when:* partner F

  - *from when:* partner I

  - *from when:* reductive defluorination

  - *from when:* reductive dechlorination

  - *from when:* reductive debromination

  - *from when:* reductive deiodination


#### sulfur reduction  `[single]`

- ↔ `forest.rule:SulfurReduction`

- **tagger rules (4):** `rule:forest-tag-sulfurreduction_disulfide`, `rule:struct-sulfur-reduction`, `rule:struct-disulfide-formation`, `rule:struct-disulfide-reduction`

- **sulfoxide** (pattern) ↔ `forest.pattern:SulfurReduction/sulfoxide`

  - `when`: `[]` partners=['O']

  - *from when:* partner O

- **disulfide** (pattern) ↔ `forest.pattern:SulfurReduction/disulfide`

  - `when`: `[]` partners=['S']

  - *from when:* partner S

- **thioether** (pattern) ↔ `forest.pattern:SulfurReduction/thioether`

  - `when`: `[{"map": 2, "z": 6}, {"map": 2, "z": 8}]` partners=['C', 'O']

  - *from when:* O-centered

  - *from when:* partner C

  - *from when:* partner O


## Tagger rules not mapped to Phase I Forest slot

- `rule:tag-sulfo-reduction` (tag)

- `rule:tag-cyanide-hydrolysis` (tag)

- `rule:tag-detoxication` (tag)

- `rule:tag-forms-reactive-conjugate` (tag)

- `rule:struct-aldehyde-oxidation` (struct)

- `rule:struct-esterification` (struct)

- `rule:struct-reduction` (struct)

- `rule:struct-decarboxylation` (struct)

- `rule:struct-dehydroxylation` (struct)

- `rule:struct-halogenation` (struct)

- `rule:struct-dehalogenation` (struct)

- `rule:struct-carboxylation` (struct)

- `rule:struct-n-nitrosation` (struct)

- `rule:struct-denitrosation` (struct)

- `rule:struct-transesterification` (struct)

- `rule:struct-dioxygenation` (struct)

- `rule:struct-desulfuration` (struct)

- `rule:struct-sulfuration` (struct)

- `rule:struct-oxidation` (struct)

- `rule:struct-lactone-hydrolysis` (struct)

- `rule:struct-azo-reduction` (struct)

- `rule:struct-cis-dihydroxylation` (struct)

- `rule:struct-alicyclic-hydroxylation` (struct)

- `rule:struct-alpha-hydroxylation` (struct)

- `rule:struct-reductive-defluorination` (struct)

- `rule:struct-sulfoxidation` (struct)

- `rule:struct-thiol-oxidation` (struct)

- `rule:struct-urea-hydrolysis` (struct)

- `rule:struct-primary-carbon-hydroxylation` (struct)

- `rule:struct-secondary-carbon-hydroxylation` (struct)

- `rule:struct-tertiary-carbon-hydroxylation` (struct)

- `rule:struct-oxime-reduction` (struct)

- `rule:struct-thiophene-epoxidation` (struct)


## Peers (not expanded)

- conjugation
- composite / multistep
