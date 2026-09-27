# xenosite-xmet — ontology authoring targets

.PHONY: ontology-stats ontology-export db-term-mapping help

ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
UV ?= uv
PY := $(UV) run python
SNAKE := $(UV) run snakemake
CORES ?= 1

help:
	@echo "Targets:"
	@echo "  make ontology-stats     XMET inventory / spine / mapping stats"
	@echo "  make ontology-export    Regenerate xmet.skos.jsonld (+ TTL) from xmet.yaml"
	@echo "  make db-term-mapping    MetXBioDB/AMD term → XMET mapping workflow"

ontology-stats:
	@$(PY) $(ROOT)/tools/ontology_stats.py

ontology-export:
	@$(PY) $(ROOT)/tools/yaml_to_skos.py
	@$(PY) $(ROOT)/tools/jsonld_to_ttl.py

db-term-mapping:
	$(SNAKE) -s $(ROOT)/workflows/db_term_mapping/Snakefile -c$(CORES)
