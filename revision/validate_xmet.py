#!/usr/bin/env python3
"""Validate the XMET YAML authoring file.

Checks are intentionally lightweight and CI-friendly. They focus on the
authoring rules that keep XMET usable as both a SKOS vocabulary and an
automation target for NLP and XenoSite-Forest reaction labeling.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import yaml


PREFERRED_SPINE_SCHEMES = {
    "xmet:reaction_class_scheme": "reaction_class",
    "xmet:product_family_scheme": "product_family",
    "xmet:structural_locus_scheme": "structural_locus",
    "xmet:pathway_role_scheme": "pathway_role",
    "xmet:disposition_stage_scheme": "disposition_stage",
    "xmet:biological_effect_scheme": "biological_effect",
    "xmet:reactive_product_potential_scheme": "reactive_product_potential",
    "xmet:text_mining_scheme": "text_mining",
    "xmet:biological_context_scheme": "biological_context",
}

ROOT_ALLOWED = {
    "xmet:0000000",
    "xmet:1100000",
    "xmet:2500000",
    "xmet:1500000",
    "xmet:1600000",
    "xmet:7500000",
    "xmet:7900000",
    "xmet:2100000",
    "xmet:3000000",
}

XMET_ID = re.compile(r"^xmet:[0-9]{7}$|^xmet:[A-Za-z_][A-Za-z0-9_]*$")
FOREST_ID = re.compile(r"^forest\.(ruleset|rule|smarts):[A-Za-z0-9_.:-]+$")
ALLOWED_SSSOM_PREDICATES = {
    "skos:exactMatch",
    "skos:closeMatch",
    "skos:broadMatch",
    "skos:narrowMatch",
    "skos:relatedMatch",
}


class Problem:
    def __init__(self, level: str, concept_id: str, message: str) -> None:
        self.level = level
        self.concept_id = concept_id
        self.message = message

    def __str__(self) -> str:
        return f"{self.level}: {self.concept_id}: {self.message}"


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def preferred_spine(concept: dict[str, Any]) -> str | None:
    explicit = concept.get("preferred_spine")
    if explicit:
        return str(explicit)

    candidates = []
    for scheme in as_list(concept.get("in_scheme")):
        if scheme in PREFERRED_SPINE_SCHEMES:
            candidates.append(PREFERRED_SPINE_SCHEMES[scheme])
    if len(candidates) == 1:
        return candidates[0]
    return None


def validate_sssom_mapping(
    mapping_path: Path,
    by_id: dict[str, dict[str, Any]],
) -> tuple[list[Problem], list[Problem]]:
    errors: list[Problem] = []
    warnings: list[Problem] = []

    if not mapping_path.exists():
        errors.append(
            Problem(
                "ERROR",
                str(mapping_path),
                "declared Forest SSSOM mapping file does not exist",
            )
        )
        return errors, warnings

    rows_seen = 0
    with mapping_path.open(newline="") as handle:
        content_lines = (line for line in handle if not line.startswith("#"))
        reader = csv.DictReader(content_lines, delimiter="\t")
        required = {"subject_id", "predicate_id", "object_id"}
        if not reader.fieldnames:
            errors.append(Problem("ERROR", str(mapping_path), "SSSOM file has no header row"))
            return errors, warnings
        missing = required.difference(reader.fieldnames)
        if missing:
            errors.append(
                Problem(
                    "ERROR",
                    str(mapping_path),
                    f"SSSOM file is missing required column(s): {', '.join(sorted(missing))}",
                )
            )
            return errors, warnings

        for i, row in enumerate(reader, start=2):
            rows_seen += 1
            subject_id = (row.get("subject_id") or "").strip()
            predicate_id = (row.get("predicate_id") or "").strip()
            object_id = (row.get("object_id") or "").strip()
            row_id = f"{mapping_path.name}:{i}"

            if not FOREST_ID.match(subject_id):
                errors.append(
                    Problem(
                        "ERROR",
                        row_id,
                        f"Forest mapping subject_id is not a recognized forest rule/ruleset/smarts CURIE: {subject_id}",
                    )
                )

            if predicate_id not in ALLOWED_SSSOM_PREDICATES:
                errors.append(
                    Problem(
                        "ERROR",
                        row_id,
                        f"SSSOM predicate should be a SKOS mapping predicate, got: {predicate_id}",
                    )
                )

            if object_id not in by_id:
                errors.append(
                    Problem(
                        "ERROR",
                        row_id,
                        f"SSSOM object_id does not exist in XMET concepts: {object_id}",
                    )
                )
            elif object_id.startswith("xmet:900"):
                errors.append(
                    Problem(
                        "ERROR",
                        row_id,
                        "Forest mapping points to deprecated in-ontology Forest mapping concept; map to a real XMET term instead",
                    )
                )

    if rows_seen == 0:
        warnings.append(Problem("WARN", str(mapping_path), "SSSOM mapping file has no mapping rows"))

    return errors, warnings


def declared_mapping_paths(data: dict[str, Any], yaml_path: Path) -> list[Path]:
    mapping_sets = data.get("mapping_sets") or {}
    paths: list[Path] = []
    for mapping in mapping_sets.values():
        if not isinstance(mapping, dict):
            continue
        file_name = mapping.get("file")
        if file_name:
            paths.append((yaml_path.parent / str(file_name)).resolve())
    return paths


def validate(path: Path, mapping_files: list[Path] | None = None) -> tuple[list[Problem], list[Problem]]:
    data = yaml.safe_load(path.read_text())
    concepts = data.get("concepts", [])
    errors: list[Problem] = []
    warnings: list[Problem] = []

    ids = [c.get("id") for c in concepts]
    counts = Counter(ids)
    for cid, n in counts.items():
        if cid is None:
            errors.append(Problem("ERROR", "<missing>", "concept is missing id"))
        elif n > 1:
            errors.append(Problem("ERROR", str(cid), f"duplicate id appears {n} times"))

    by_id = {c.get("id"): c for c in concepts if c.get("id")}
    children: dict[str, list[str]] = defaultdict(list)
    for c in concepts:
        cid = c.get("id")
        for p in as_list(c.get("parents")):
            children[p].append(cid)

    for c in concepts:
        cid = c.get("id", "<missing>")
        if not isinstance(cid, str) or not XMET_ID.match(cid):
            errors.append(Problem("ERROR", str(cid), "id is not a valid xmet CURIE"))

        if not c.get("pref_label") and not c.get("preferred_label"):
            errors.append(Problem("ERROR", str(cid), "missing pref_label/preferred_label"))

        if not c.get("definition"):
            warnings.append(Problem("WARN", str(cid), "missing definition"))

        schemes = as_list(c.get("in_scheme"))
        if not schemes:
            errors.append(Problem("ERROR", str(cid), "missing in_scheme"))

        spine = preferred_spine(c)
        if spine is None:
            errors.append(
                Problem(
                    "ERROR",
                    str(cid),
                    "preferred_spine is ambiguous; add preferred_spine explicitly",
                )
            )

        parents = as_list(c.get("parents"))
        for parent_id in parents:
            if parent_id not in by_id:
                errors.append(Problem("ERROR", str(cid), f"parent does not exist: {parent_id}"))
                continue
            parent = by_id[parent_id]
            parent_spine = preferred_spine(parent)
            if spine and parent_spine and spine != parent_spine:
                errors.append(
                    Problem(
                        "ERROR",
                        str(cid),
                        f"parent {parent_id} is in spine {parent_spine}, but concept preferred spine is {spine}; use a facet/mapping property instead of parents",
                    )
                )

        if len(parents) > 1:
            warnings.append(
                Problem(
                    "WARN",
                    str(cid),
                    "multiple preferred parents; make sure this is real hierarchy, not cross-cutting tags",
                )
            )

        if (
            parents
            and parents[0] in ROOT_ALLOWED
            and cid not in ROOT_ALLOWED
            and not children.get(cid)
        ):
            # A leaf directly under a broad root usually signals that an
            # intermediate grouping term is missing. Grouping concepts directly
            # under a broad root are expected.
            warnings.append(
                Problem(
                    "WARN",
                    str(cid),
                    f"direct child of broad root {parents[0]}; confirm no intermediate parent is needed",
                )
            )

        # Phase and activation language should not be preferred hierarchy parents
        # for reaction classes.
        for forbidden in ("xmet:0000001", "xmet:0000002", "xmet:0003000"):
            if forbidden in parents and spine == "reaction_class":
                errors.append(
                    Problem(
                        "ERROR",
                        str(cid),
                        f"reaction class uses {forbidden} as a parent; use hasDispositionStage or hasBiologicalEffect",
                    )
                )

    for parent_id, child_ids in children.items():
        if len(child_ids) > 25:
            warnings.append(
                Problem(
                    "WARN",
                    parent_id,
                    f"{len(child_ids)} direct children; hierarchy may be too flat",
                )
            )

    paths_to_check = mapping_files if mapping_files is not None else declared_mapping_paths(data, path)
    for mapping_path in paths_to_check:
        mapping_errors, mapping_warnings = validate_sssom_mapping(mapping_path, by_id)
        errors.extend(mapping_errors)
        warnings.extend(mapping_warnings)

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("yaml_file", type=Path)
    parser.add_argument(
        "--mapping-file",
        action="append",
        type=Path,
        help="Optional SSSOM mapping file to validate. Defaults to mapping_sets declared in the YAML.",
    )
    parser.add_argument("--warnings-as-errors", action="store_true")
    args = parser.parse_args()

    errors, warnings = validate(args.yaml_file, args.mapping_file)
    for p in errors + warnings:
        print(p)

    print(f"\nSummary: {len(errors)} error(s), {len(warnings)} warning(s)")
    if errors or (args.warnings_as_errors and warnings):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
