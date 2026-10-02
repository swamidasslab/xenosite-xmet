# xenosite-xmet — ontology authoring targets

.PHONY: ontology-stats ontology-export ontology-tree ontology-tree-biotransformer ontology-fuzzy-audit forest-pattern-coverage db-term-mapping validate-redesign rebuild-tagger-sssom sync-tagger-emits biotransformer-inventory biotransformer-rule-smarts help

ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
UV ?= uv
PY := $(UV) run python
SNAKE := $(UV) run snakemake
CORES ?= 1

help:
	@echo "Targets:"
	@echo "  make ontology-stats      XMET inventory / spine / mapping stats"
	@echo "  make ontology-tree       Pretty-print full XMET tree (+ Forest SSSOM)"
	@echo "  make ontology-tree-biotransformer  XMET tree pruned to BioTransformer SSSOM (common_name + class)"
	@echo "  make biotransformer-inventory  Refresh BT reaction-type inventory TSV"
	@echo "  make biotransformer-rule-smarts  Export BT reactant/exclusion SMARTS + SMIRKS"
	@echo "  make forest-pattern-coverage  SPARQL Forest rule↔pattern cover stats (from scratch)"
	@echo "  make ontology-fuzzy-audit  Fuzzy label scan for duplicates / misparenting"
	@echo "  make ontology-export     Regenerate xmet.skos.jsonld + xmet.ttl from xmet.yaml"
	@echo "  make db-term-mapping     MetXBioDB/AMD term → XMET mapping workflow"
	@echo "  make validate-redesign   Redesign v1 adherence (Forest/tagger SSSOM, spines, remap)"
	@echo "  make rebuild-tagger-sssom  Refresh xmet-tagger.sssom.tsv from tagger SMARTS emits"
	@echo "  make sync-tagger-emits     Rewrite sibling tagger emits from xmet-tagger.sssom"
	@echo "  make site-data           Generate website data + w3id .htaccess from site.config.yaml"
	@echo "  make site                Build the static website into site/dist"
	@echo "  make site-serve          Run the website dev server"

ontology-stats:
	@$(PY) $(ROOT)/tools/ontology_stats.py

ontology-tree:
	@$(PY) $(ROOT)/tools/print_xmet_tree.py --ids --stats

ontology-tree-biotransformer:
	@$(PY) $(ROOT)/tools/print_xmet_tree.py --ids --stats --no-forest --no-tagger --bt-only --no-relations

biotransformer-inventory:
	@$(PY) $(ROOT)/tools/inventory_biotransformer.py

biotransformer-rule-smarts:
	@$(PY) $(ROOT)/tools/export_biotransformer_rule_smarts.py

forest-pattern-coverage:
	@# Always rebuild SKOS TTL, then SPARQL-infer covers from TTL + SSSOM (no cache).
	@$(PY) $(ROOT)/tools/jsonld_to_ttl.py
	@$(PY) $(ROOT)/tools/forest_pattern_coverage.py --json

ontology-fuzzy-audit:
	@$(PY) $(ROOT)/tools/fuzzy_ontology_audit.py

ontology-export:
	@$(PY) $(ROOT)/tools/yaml_to_skos.py
	@$(PY) $(ROOT)/tools/jsonld_to_ttl.py

db-term-mapping:
	$(SNAKE) -s $(ROOT)/workflows/db_term_mapping/Snakefile -c$(CORES)

validate-redesign:
	@$(PY) $(ROOT)/tools/validate_redesign_v1.py

sync-tagger-emits:
	@$(PY) $(ROOT)/tools/sync_tagger_emits_from_sssom.py

rebuild-tagger-sssom:
	@$(PY) $(ROOT)/tools/rebuild_tagger_sssom.py

# --- Vocabulary website (generic generator in tools/sitegen, Astro site in site/) ---

.PHONY: site-data site site-serve

site-data:
	@$(PY) $(ROOT)/tools/sitegen/build.py --config $(ROOT)/site.config.yaml

site: site-data
	@cd $(ROOT)/site && npm ci --silent && npm run build

site-serve: site-data
	@cd $(ROOT)/site && npm install --silent && npm run dev
