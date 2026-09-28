# xenosite-xmet — ontology authoring targets

.PHONY: ontology-stats ontology-export ontology-tree ontology-fuzzy-audit db-term-mapping validate-redesign rebuild-tagger-sssom help

ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
UV ?= uv
PY := $(UV) run python
SNAKE := $(UV) run snakemake
CORES ?= 1

help:
	@echo "Targets:"
	@echo "  make ontology-stats      XMET inventory / spine / mapping stats"
	@echo "  make ontology-tree       Pretty-print full XMET tree (+ Forest SSSOM)"
	@echo "  make ontology-fuzzy-audit  Fuzzy label scan for duplicates / misparenting"
	@echo "  make ontology-export     Regenerate xmet.skos.jsonld (+ TTL) from xmet.yaml"
	@echo "  make db-term-mapping     MetXBioDB/AMD term → XMET mapping workflow"
	@echo "  make validate-redesign   Redesign v1 adherence (Forest/tagger SSSOM, spines, remap)"
	@echo "  make rebuild-tagger-sssom  Refresh xmet-tagger.sssom.tsv from tagger SMARTS emits"

ontology-stats:
	@$(PY) $(ROOT)/tools/ontology_stats.py

ontology-tree:
	@$(PY) $(ROOT)/tools/print_xmet_tree.py --ids --stats

ontology-fuzzy-audit:
	@$(PY) $(ROOT)/tools/fuzzy_ontology_audit.py

ontology-export:
	@$(PY) $(ROOT)/tools/yaml_to_skos.py
	@$(PY) $(ROOT)/tools/jsonld_to_ttl.py

db-term-mapping:
	$(SNAKE) -s $(ROOT)/workflows/db_term_mapping/Snakefile -c$(CORES)

validate-redesign:
	@$(PY) $(ROOT)/tools/validate_redesign_v1.py

rebuild-tagger-sssom:
	@$(PY) $(ROOT)/tools/rebuild_tagger_sssom.py

