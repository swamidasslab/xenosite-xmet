#!/usr/bin/env python3
"""Validate XMET redesign v1 locked goals.

Hard failures unless listed in data/mappings/validation-xfail.tsv.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
YAML_PATH = ROOT / "data/ontology/xmet.yaml"
REMAP_PATH = ROOT / "data/mappings/xmet-id-remap.tsv"
FOREST_SSSOM = ROOT / "data/mappings/xmet-forest.sssom.tsv"
EXTERNAL_SSSOM = ROOT / "data/mappings/xmet-external.sssom.tsv"
MOP_SSSOM = ROOT / "data/mappings/xmet-mop.sssom.tsv"
MESH_SSSOM = ROOT / "data/mappings/xmet-mesh.sssom.tsv"
TAGGER_SSSOM = ROOT / "data/mappings/xmet-tagger.sssom.tsv"
XFAIL_PATH = ROOT / "data/mappings/validation-xfail.tsv"
DRAFT_PHASE1 = ROOT / "revision/draft-reaction-class-phase1-tree.json"
BASELINE_EXTERNAL = ROOT / "artifacts" / "xmet-external.sssom.pre-redesign-v1.tsv"
ALLOWED_RULE_PATTERN_PREDS = {"skos:exactMatch", "skos:closeMatch"}

# Product / model names forbidden in chemical concept definitions.
DEFINITION_PRODUCT_REF_RE = re.compile(
    r"(?i)\b(?:metabolic\s+)?forest\b|forest\.|forest-map|\brainbow\b|"
    r"\bxenosite\b|xenosite[.\-]"
)

DISPOSITION = "xmet:4000212"
REACTION_CLASS = "xmet:4000213"
REACTION_DESCRIPTOR = "xmet:4000263"
CONCEPT_RELATION = "xmet:4000281"
OXIDATION = "xmet:4000009"
SO = "xmet:4000004"
UO = "xmet:4000005"
DH = "xmet:4000006"
HD = "xmet:4000007"
RD = "xmet:4000008"
CONJUGATION = "xmet:4000011"
TRANSFER = "xmet:4000266"
ADDUCT = "xmet:4000267"
GSH = "xmet:4000167"
PHASE_I = "xmet:4000001"
PHASE_II = "xmet:4000002"
PHASE_III = "xmet:4000003"
PHASE_I_FAMILY = "xmet:1200000"
PHASE_II_FAMILY = "xmet:1300000"
REARRANGEMENT = "xmet:4000190"
TAUTOMERIZATION = "xmet:4000186"
ISOMERIZATION = "xmet:4000189"

COLORS = {SO, UO, DH, HD, RD}
PHASE_TAGS = {PHASE_I, PHASE_II, PHASE_III, "xmet:4000264"}
ISOREDOX = "xmet:4000265"

# Historical two-letter ruleset codes → long xf: catalog / leaf names.
# SSSOM must use long names only (never SO/UO/CJ/…).
SHORT_TO_LONG: dict[str, str] = {
    "SO": "StableOxygenation",
    "UO": "UnstableOxygenation",
    "DH": "Dehydrogenation",
    "HD": "Hydrolysis",
    "RD": "Reduction",
    "CJ": "Conjugation",
    "QF": "QuinoneFormation",
    "TT": "Tautomerization",
}

# Catalogs that may use skos:relatedMatch (not rule/pattern exactMatch homes).
RELATEDMATCH_CATALOGS: frozenset[str] = frozenset(
    {
        "PhaseOne",
        "StableOxygenation",
        "UnstableOxygenation",
        "Reduction",
        "Conjugation",  # deferred until catalog is ready; allow when present
    }
)

# Color / conjugation membership beyond draft PhaseOne colors (specialized leaves).
EXTRA_RULE_TO_RULESET: dict[str, str] = {
    "NDealkylation": "xf:UnstableOxygenation",
    "AzoSplitting": "xf:Reduction",
    "BenzodioxoleReduction": "xf:Reduction",
    "NitroaromaticReduction": "xf:Reduction",
    "ThiopheneSulfurOxidation": "xf:StableOxygenation",
}
CJ_RULES = ("Acetylation", "Sulfation", "Glucuronidation", "Glutathionation")

# Rules whose Forest color membership is operational only — chemical parent may
# differ (no multi-inheritance). Nesting under the ruleset home is not required.
OPERATIONAL_RULESET_MEMBERSHIP_ONLY = {
    "xf:Dehydration",  # chemically elimination / isoredox; Forest lists under RD
    "xf:EpoxideOpening",  # chemically isoredox ring opening; Forest lists under HD
}

# Closest chemist parent each Forest catalog home must nest under (or equal).
RULESET_REQUIRED_ANCESTOR: dict[str, str] = {
    "xf:StableOxygenation": OXIDATION,
    "xf:UnstableOxygenation": OXIDATION,
    "xf:Reduction": REACTION_CLASS,
    "xf:PhaseOne": DISPOSITION,
}


# Catalog segments that may prefix a rule in Forest path-form CURIEs
# (``xf:PhaseOne/StableOxygenation/Hydroxylation/h`` → ``xf:Hydroxylation/h``).
CATALOG_PATH_SEGMENTS: frozenset[str] = frozenset(
    {"PhaseOne", "StableOxygenation", "UnstableOxygenation", "Dehydrogenation",
     "Hydrolysis", "Reduction", "Conjugation"}
)


def strip_catalog_path(local: str) -> str:
    """Drop leading catalog segments from a path-form local name.

    A catalog segment is dropped only when the next segment is another catalog or
    rule (capitalized), never when it is a pattern — so ``PhaseOne/Dehydrogenation``
    → ``Dehydrogenation`` and ``PhaseOne/Dehydrogenation/Dehydrogenation`` →
    ``Dehydrogenation``, while flat ``Rule/pattern`` forms are unchanged.
    """
    segs = local.split("/")
    while len(segs) > 1 and segs[0] in CATALOG_PATH_SEGMENTS and segs[1][:1].isupper():
        segs = segs[1:]
    return "/".join(segs)


def normalize_forest_object(obj: str) -> str:
    """Canonical ``xf:`` CURIE from ``xf:`` (flat or catalog-path) or legacy ``forest.*`` forms.

    Short catalog codes (SO/UO/…) expand to long names. Patterns keep ``Rule/pat``.
    """
    raw = (obj or "").strip()
    if not raw:
        return raw
    if raw.startswith("xf:"):
        local = raw[3:]
    elif raw.startswith("forest.pattern:"):
        local = raw[len("forest.pattern:") :]
    elif raw.startswith("forest.rule:"):
        local = raw[len("forest.rule:") :]
    elif raw.startswith("forest.ruleset:"):
        local = raw[len("forest.ruleset:") :]
    else:
        return raw
    local = strip_catalog_path(local)
    if "/" not in local and local in SHORT_TO_LONG:
        local = SHORT_TO_LONG[local]
    return f"xf:{local}"


def forest_object_kind(obj: str) -> str:
    """Return ``pattern``, ``catalog``, ``rule``, or ``other`` for a Forest object id."""
    n = normalize_forest_object(obj)
    if not n.startswith("xf:"):
        return "other"
    local = n[3:]
    if "/" in local:
        return "pattern"
    if local in RELATEDMATCH_CATALOGS:
        return "catalog"
    return "rule"


def xf_rule(name: str) -> str:
    return f"xf:{name}"


def is_relatedmatch_catalog(obj: str) -> bool:
    n = normalize_forest_object(obj)
    return forest_object_kind(n) == "catalog"


class Finding:
    def __init__(self, check_id: str, subject_id: str, message: str, object_id: str = "") -> None:
        self.check_id = check_id
        self.subject_id = subject_id
        self.object_id = object_id
        self.message = message

    def key(self) -> tuple[str, str, str]:
        return (self.check_id, self.subject_id, self.object_id)

    def __str__(self) -> str:
        obj = f" → {self.object_id}" if self.object_id else ""
        return f"[{self.check_id}] {self.subject_id}{obj}: {self.message}"


def load_yaml() -> dict[str, Any]:
    return yaml.safe_load(YAML_PATH.read_text())


def by_id(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {c["id"]: c for c in data["concepts"]}


def parents_map(data: dict[str, Any]) -> dict[str, list[str]]:
    return {c["id"]: list(c.get("parents") or []) for c in data["concepts"]}


def children_map(pm: dict[str, list[str]]) -> dict[str, list[str]]:
    ch: dict[str, list[str]] = defaultdict(list)
    for cid, ps in pm.items():
        for p in ps:
            ch[p].append(cid)
    return ch


def ancestors(cid: str, pm: dict[str, list[str]], memo: dict[str, set[str]] | None = None) -> set[str]:
    if memo is None:
        memo = {}
    if cid in memo:
        return memo[cid]
    out: set[str] = set()
    for p in pm.get(cid, []):
        out.add(p)
        out |= ancestors(p, pm, memo)
    memo[cid] = out
    return out


def load_xfail() -> set[tuple[str, str, str]]:
    if not XFAIL_PATH.exists():
        return set()
    rows: set[tuple[str, str, str]] = set()
    with XFAIL_PATH.open() as fh:
        reader = csv.DictReader((ln for ln in fh if not ln.startswith("#")), delimiter="\t")
        for row in reader:
            rows.add(
                (
                    (row.get("check_id") or "").strip(),
                    (row.get("subject_id") or "").strip(),
                    (row.get("object_id") or "").strip(),
                )
            )
    return rows


def load_sssom(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open() as fh:
        reader = csv.DictReader((ln for ln in fh if not ln.startswith("#")), delimiter="\t")
        rows = list(reader)
    # Canonicalize Forest object CURIEs to xf: (accept legacy forest.*).
    if path.resolve() == FOREST_SSSOM.resolve():
        for r in rows:
            obj = r.get("object_id") or ""
            if obj.startswith(("xf:", "forest.")):
                r["object_id"] = normalize_forest_object(obj)
    return rows


def index_sssom_by_object(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    by_obj: dict[str, list[dict[str, str]]] = defaultdict(list)
    for r in rows:
        by_obj[r["object_id"]].append(r)
    return by_obj


def chemist_sssom_homes(
    by_obj: dict[str, list[dict[str, str]]], object_id: str
) -> list[str]:
    """Non-alias XMET subjects mapped to a Forest object."""
    out: list[str] = []
    seen: set[str] = set()
    for r in by_obj.get(object_id) or []:
        sub = r["subject_id"]
        if sub.startswith("xmet:9") or sub in seen:
            continue
        seen.add(sub)
        out.append(sub)
    return out


def under_or_equal(cid: str, ancestor: str, pm: dict[str, list[str]], memo: dict[str, set[str]]) -> bool:
    return cid == ancestor or ancestor in ancestors(cid, pm, memo)


def load_rule_to_ruleset_membership() -> dict[str, str]:
    """xf:Rule → xf:Catalog from draft colors + curated extras + conjugation leaves."""
    membership: dict[str, str] = {}
    if DRAFT_PHASE1.exists():
        draft = json.loads(DRAFT_PHASE1.read_text())
        for color in (draft.get("reaction_class") or {}).get("phase_one_colors") or []:
            rs = normalize_forest_object(color.get("forest_ruleset") or "")
            for rule in color.get("rules") or []:
                fr = normalize_forest_object(rule.get("forest_rule") or "")
                if fr.startswith("xf:") and rs.startswith("xf:"):
                    membership[fr] = rs
    for rule_name, rs in EXTRA_RULE_TO_RULESET.items():
        membership.setdefault(xf_rule(rule_name), rs)
    for rule_name in CJ_RULES:
        membership.setdefault(xf_rule(rule_name), "xf:Conjugation")
    for fr in OPERATIONAL_RULESET_MEMBERSHIP_ONLY:
        membership.pop(fr, None)
    return membership


def check_single_parent(
    findings: list[Finding],
    concepts: dict[str, dict[str, Any]],
) -> None:
    """XMET forbids multi-inheritance: at most one skos:broader parent."""
    for cid, c in concepts.items():
        parents = c.get("parents") or []
        if len(parents) > 1:
            findings.append(
                Finding(
                    "single_parent",
                    cid,
                    f"multi-inheritance forbidden; parents={parents}",
                )
            )


def check_unique_sssom_homes(
    findings: list[Finding],
    rows: list[dict[str, str]],
    *,
    object_prefix: str = "",
    object_kind: str | None = None,
    check_id: str,
    label: str,
) -> None:
    """Each Forest/tagger object may have only one XMET home (object → subject)."""
    by_obj: dict[str, list[dict[str, str]]] = defaultdict(list)
    for r in rows:
        obj = r.get("object_id") or ""
        if object_kind is not None:
            if forest_object_kind(obj) != object_kind:
                continue
        elif object_prefix and not obj.startswith(object_prefix):
            continue
        by_obj[obj].append(r)
    for obj, mapped in sorted(by_obj.items()):
        subjects = sorted({r["subject_id"] for r in mapped})
        if len(subjects) > 1:
            findings.append(
                Finding(
                    check_id,
                    subjects[0],
                    f"{label} mapped to multiple XMET homes: {', '.join(subjects)}",
                    obj,
                )
            )


def check_unique_sssom_subjects(
    findings: list[Finding],
    rows: list[dict[str, str]],
    *,
    object_prefix: str = "",
    object_kind: str | None = None,
    check_id: str,
    label: str,
) -> None:
    """Each XMET home may map to at most one object in a peer class (subject → object).

    Peer classes: pattern↔pattern, rule↔rule, tagger rule:↔rule:.
    Cross-class co-homes (pattern+rule on one concept) are OK.
    """
    by_sub: dict[str, list[str]] = defaultdict(list)
    for r in rows:
        obj = r.get("object_id") or ""
        if object_kind is not None:
            if forest_object_kind(obj) != object_kind:
                continue
        elif not obj.startswith(object_prefix):
            continue
        by_sub[r["subject_id"]].append(obj)
    for sub, objs in sorted(by_sub.items()):
        uniq = sorted(set(objs))
        if len(uniq) > 1:
            findings.append(
                Finding(
                    check_id,
                    sub,
                    f"{label} home shared by multiple objects: {', '.join(uniq)}",
                    uniq[0],
                )
            )


def check_definition_no_product_refs(
    findings: list[Finding], concepts: dict[str, dict[str, Any]]
) -> None:
    """Definitions must describe chemistry, not Forest / Xenosite / Rainbow tooling."""
    for cid, c in concepts.items():
        text = c.get("definition") or ""
        if not isinstance(text, str):
            continue
        for m in DEFINITION_PRODUCT_REF_RE.finditer(text):
            findings.append(
                Finding(
                    "definition_product_ref",
                    cid,
                    f"definition mentions product/tooling {m.group(0)!r} "
                    f"(keep chemical concept wording only)",
                )
            )


def check_remap(findings: list[Finding], concepts: dict[str, dict[str, Any]]) -> None:
    if not REMAP_PATH.exists():
        return
    with REMAP_PATH.open() as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        for row in reader:
            old = (row.get("old_id") or "").strip()
            new = (row.get("new_id") or "").strip()
            ctype = (row.get("change_type") or "").strip()
            if ctype == "relabeled" and old == new:
                continue
            if old and old == new:
                continue
            if old and old in concepts and ctype in {"moved", "retired", "split", "merged"} and old != new:
                # old must leave live YAML when superseded by a different id
                if new and old != new:
                    findings.append(
                        Finding(
                            "remap_old_absent",
                            old,
                            f"old_id still present in live YAML (change_type={ctype})",
                            new,
                        )
                    )
            if new and new not in concepts:
                findings.append(
                    Finding("remap_new_present", new, "new_id missing from live YAML", old)
                )
            if new.startswith("xmet:3") or new.startswith("xmet:4"):
                pass
            elif ctype == "moved" and new and new != old:
                findings.append(
                    Finding(
                        "remap_generation_block",
                        new,
                        "moved/new id should be redesign-generation xmet:3xxxxxx/4xxxxxx",
                        old,
                    )
                )


def check_disposition_not_chem_parent(findings: list[Finding], pm: dict[str, list[str]]) -> None:
    for cid in COLORS | {OXIDATION, CONJUGATION, REARRANGEMENT}:
        anc = ancestors(cid, pm)
        if anc & PHASE_TAGS:
            findings.append(
                Finding(
                    "disposition_not_chem_parent",
                    cid,
                    f"reaction-class concept has disposition tag ancestor(s) {sorted(anc & PHASE_TAGS)}",
                )
            )
        if PHASE_I_FAMILY in anc or PHASE_II_FAMILY in anc:
            findings.append(
                Finding(
                    "legacy_family_not_chem_parent",
                    cid,
                    "concept descends from legacy phase I/II family spine",
                )
            )


def check_five_colors_and_conjugation(
    findings: list[Finding],
    concepts: dict[str, dict[str, Any]],
    pm: dict[str, list[str]],
) -> None:
    for cid, label in [
        (SO, "stable oxygenation"),
        (UO, "unstable oxygenation"),
        (DH, "dehydrogenation"),
        (HD, "hydrolysis"),
        (RD, "reduction"),
    ]:
        if cid not in concepts:
            findings.append(Finding("five_colors_present", cid, f"missing {label}"))
            continue
        if concepts[cid]["preferred_label"] != label and label not in (
            concepts[cid].get("synonyms") or []
        ):
            # allow slight label drift only if preferred matches
            if concepts[cid]["preferred_label"] != label:
                findings.append(
                    Finding(
                        "five_colors_present",
                        cid,
                        f"expected preferred_label {label!r}, got {concepts[cid]['preferred_label']!r}",
                    )
                )
    # SO/UO/DH under oxidation; RD is reduction class; HD under isoredox
    if OXIDATION not in ancestors(SO, pm) and OXIDATION not in pm.get(SO, []):
        findings.append(Finding("oxidation_groups_so_uo", SO, "stable oxygenation not under oxidation"))
    if OXIDATION not in ancestors(UO, pm) and OXIDATION not in pm.get(UO, []):
        findings.append(Finding("oxidation_groups_so_uo", UO, "unstable oxygenation not under oxidation"))
    if OXIDATION not in ancestors(DH, pm) and OXIDATION not in pm.get(DH, []):
        findings.append(Finding("oxidation_groups_dh", DH, "dehydrogenation not under oxidation"))
    if REACTION_CLASS not in ancestors(OXIDATION, pm) and REACTION_CLASS not in pm.get(OXIDATION, []):
        findings.append(Finding("oxidation_under_reaction_class", OXIDATION, "oxidation not under reaction class"))
    if REACTION_CLASS not in ancestors(RD, pm) and REACTION_CLASS not in pm.get(RD, []):
        findings.append(Finding("reduction_under_reaction_class", RD, "reduction not under reaction class"))
    isoredox = "xmet:4000265"
    if isoredox not in concepts:
        findings.append(Finding("isoredox_present", isoredox, "missing isoredox class"))
    else:
        if REACTION_CLASS not in pm.get(isoredox, []):
            findings.append(Finding("isoredox_under_reaction_class", isoredox, "isoredox not under reaction class"))
        if isoredox not in pm.get(HD, []) and isoredox not in ancestors(HD, pm):
            findings.append(Finding("hydrolysis_under_isoredox", HD, "hydrolysis not under isoredox"))
    for cid in (CONJUGATION, REARRANGEMENT):
        if REACTION_CLASS not in ancestors(cid, pm) and REACTION_CLASS not in pm.get(cid, []):
            findings.append(
                Finding("color_under_reaction_class", cid, "not under reaction class")
            )
    if TRANSFER not in concepts or ADDUCT not in concepts:
        findings.append(Finding("conjugation_fork", TRANSFER, "missing transfer/adduct fork nodes"))
    else:
        if CONJUGATION not in pm.get(TRANSFER, []):
            findings.append(Finding("conjugation_fork", TRANSFER, "transfer not under conjugation"))
        if CONJUGATION not in pm.get(ADDUCT, []):
            findings.append(Finding("conjugation_fork", ADDUCT, "adduct formation not under conjugation"))
    if GSH in concepts:
        anc = ancestors(GSH, pm) | set(pm.get(GSH, []))
        if ADDUCT not in anc:
            findings.append(Finding("gsh_under_adducts", GSH, "GSH not under adduct formation"))
        if TRANSFER in anc:
            findings.append(Finding("gsh_not_under_transfer", GSH, "GSH must not hang under transfer conjugation"))
    if TAUTOMERIZATION in concepts and REARRANGEMENT not in (
        set(pm.get(TAUTOMERIZATION, [])) | ancestors(TAUTOMERIZATION, pm)
    ):
        findings.append(
            Finding("rearrangement_nesting", TAUTOMERIZATION, "tautomerization not under rearrangement")
        )
    if ISOMERIZATION in concepts and REARRANGEMENT not in (
        set(pm.get(ISOMERIZATION, [])) | ancestors(ISOMERIZATION, pm)
    ):
        findings.append(
            Finding("rearrangement_nesting", ISOMERIZATION, "isomerization not under rearrangement")
        )


def check_descriptor_orthogonal(
    findings: list[Finding], concepts: dict[str, dict[str, Any]], pm: dict[str, list[str]]
) -> None:
    if REACTION_DESCRIPTOR not in concepts:
        findings.append(
            Finding("descriptor_spine", REACTION_DESCRIPTOR, "missing reaction descriptor concept")
        )
        return
    # Backbone reaction-class nodes must not descend from reaction descriptor.
    backbone = COLORS | {OXIDATION, CONJUGATION, REARRANGEMENT, "xmet:4000265", RD, HD, DH}
    for cid in backbone:
        if cid not in concepts:
            continue
        anc = ancestors(cid, pm)
        if REACTION_DESCRIPTOR in anc:
            findings.append(
                Finding(
                    "descriptor_orthogonal",
                    cid,
                    "reaction-class backbone descends from reaction descriptor",
                )
            )


def check_redundant_soft_targets(
    findings: list[Finding],
    concepts: dict[str, dict[str, Any]],
    pm: dict[str, list[str]],
) -> None:
    """suggests / always_with: do not list a target that is under another listed target.

    Within one precision level, the parent covers descendants (e.g. halide LG →
    oxidative dehalogenation already covers ox-dehal-to-alcohol). Halogen-specific
    LGs should point at halogen-specific reactions instead of also listing the
    generic parent (precision matching) — then no parent+child pair appears.
    """
    memo: dict[str, set[str]] = {}
    for cid, c in concepts.items():
        for field in ("suggests", "always_with"):
            vals = c.get(field) or []
            if len(vals) < 2:
                continue
            # detect dupes
            seen: set[str] = set()
            for t in vals:
                if t in seen:
                    findings.append(
                        Finding(
                            "soft_target_redundant",
                            cid,
                            f"duplicate {field} target {t}",
                            t,
                        )
                    )
                seen.add(t)
            uniq = list(dict.fromkeys(vals))
            for a in uniq:
                if a not in concepts:
                    continue
                for b in uniq:
                    if a == b or b not in concepts:
                        continue
                    if under_or_equal(b, a, pm, memo):
                        findings.append(
                            Finding(
                                "soft_target_redundant",
                                cid,
                                f"{field} target {b} is under listed {a}; keep parent only",
                                b,
                            )
                        )


def check_relation_vocab(findings: list[Finding], concepts: dict[str, dict[str, Any]]) -> None:
    required = {
        "xmet:4000282": ("related to", "skos:related"),
        "xmet:4000285": ("has part", "dcterms:hasPart"),
        "xmet:4000286": ("is part of", "dcterms:isPartOf"),
    }
    for cid, (label, exact) in required.items():
        if cid not in concepts:
            findings.append(Finding("relation_vocab", cid, f"missing {label}"))
            continue
        if concepts[cid]["preferred_label"] != label:
            findings.append(
                Finding(
                    "relation_vocab",
                    cid,
                    f"expected label {label!r}, got {concepts[cid]['preferred_label']!r}",
                )
            )
        em = concepts[cid].get("exact_match") or []
        if exact not in em:
            findings.append(
                Finding("relation_vocab_exact", cid, f"missing exact_match {exact}", exact)
            )
    for cid in ("xmet:4000283", "xmet:4000284"):
        if cid not in concepts:
            findings.append(Finding("relation_vocab", cid, "missing suggests/always with"))
    for cid, label in (
        ("xmet:4000414", "operationalizes"),
        ("xmet:4000415", "predicts"),
        ("xmet:4000416", "recognizes"),
        ("xmet:4000417", "enumerates"),
    ):
        if cid not in concepts:
            findings.append(Finding("relation_vocab", cid, f"missing {label}"))
        elif concepts[cid].get("preferred_label") != label:
            findings.append(
                Finding(
                    "relation_vocab",
                    cid,
                    f"expected label {label!r}, got {concepts[cid].get('preferred_label')!r}",
                )
            )


def check_dealkylation_pattern_always_with(
    findings: list[Finding],
    concepts: dict[str, dict[str, Any]],
    pm: dict[str, list[str]],
) -> None:
    """Dealkylation / N-dealkylation patterns may share a site home iff alwaysWith distinguishes them.

    Policy for ``xf:Dealkylation/*`` and ``xf:NDealkylation/*``:
    - Every such SSSOM row must list ``always_with`` descriptor CURIEs (pipe-separated)
      under reaction descriptor.
    - Patterns that share the same subject_id must have distinct always_with sets.
    """
    rows = load_sssom(FOREST_SSSOM)
    prefixes = ("xf:Dealkylation/", "xf:NDealkylation/")
    d_rows = [
        r
        for r in rows
        if any((r.get("object_id") or "").startswith(p) for p in prefixes)
    ]
    if not d_rows:
        findings.append(
            Finding(
                "dealk_always_with",
                "xmet:4000042",
                "no Forest Dealkylation/NDealkylation pattern SSSOM rows found",
            )
        )
        return

    memo: dict[str, set[str]] = {}
    by_home: dict[str, list[dict[str, str]]] = defaultdict(list)

    for r in d_rows:
        obj = r.get("object_id") or ""
        sub = r.get("subject_id") or ""
        raw_aw = (r.get("always_with") or "").strip()
        aw = [x.strip() for x in raw_aw.split("|") if x.strip()]

        if not aw:
            findings.append(
                Finding(
                    "dealk_always_with",
                    sub or obj,
                    "Dealkylation/NDealkylation pattern mapping missing always_with descriptors",
                    obj,
                )
            )
            continue

        bad_targets: list[str] = []
        for cid in aw:
            if cid not in concepts:
                bad_targets.append(f"{cid}(missing)")
                continue
            if cid != REACTION_DESCRIPTOR and REACTION_DESCRIPTOR not in ancestors(
                cid, pm, memo
            ):
                bad_targets.append(f"{cid}(not under reaction descriptor)")
        if bad_targets:
            findings.append(
                Finding(
                    "dealk_always_with",
                    sub or obj,
                    "always_with targets must be reaction-descriptor concepts: "
                    + ", ".join(bad_targets),
                    obj,
                )
            )

        if sub:
            by_home[sub].append(r)

    for sub, group in sorted(by_home.items()):
        if len(group) < 2:
            continue
        # Distinct always_with within one family (Dealkylation or NDealkylation).
        # Cross-family twins (Dealkylation/X ↔ NDealkylation/X) may share always_with.
        for family_prefix in ("xf:Dealkylation/", "xf:NDealkylation/"):
            fam = [r for r in group if (r.get("object_id") or "").startswith(family_prefix)]
            seen: dict[frozenset[str], str] = {}
            for r in fam:
                obj = r.get("object_id") or ""
                aw = frozenset(
                    x.strip()
                    for x in (r.get("always_with") or "").split("|")
                    if x.strip()
                )
                if not aw:
                    continue
                prior = seen.get(aw)
                if prior:
                    findings.append(
                        Finding(
                            "dealk_always_with_distinct",
                            sub,
                            f"patterns share home with identical always_with {sorted(aw)}: "
                            f"{prior} and {obj}",
                            obj,
                        )
                    )
                else:
                    seen[aw] = obj


def check_ndealkylation_pattern_always_with(
    findings: list[Finding],
    concepts: dict[str, dict[str, Any]],
    pm: dict[str, list[str]],
) -> None:
    """Backward-compatible alias — full policy is check_dealkylation_pattern_always_with."""
    check_dealkylation_pattern_always_with(findings, concepts, pm)

def check_forest_nesting(
    findings: list[Finding],
    concepts: dict[str, dict[str, Any]],
    pm: dict[str, list[str]],
) -> None:
    """Forest hierarchy mirrored in XMET: pattern ⊂ rule ⊂ catalog ⊂ parent.

    1. Every mapped ``xf:Rule/pat`` chemist home nests under the mapped ``xf:Rule``
       chemist home.
    2. Every rule with a known catalog membership nests under (or equals) at
       least one chemist home of that catalog.
    3. Every catalog chemist home nests under its required reaction-class /
       disposition ancestor; Conjugation homes nest under conjugation (or are it)
       when a Conjugation relatedMatch row is present (catalog deferred otherwise).
    """
    rows = load_sssom(FOREST_SSSOM)
    by_obj = index_sssom_by_object(rows)

    memo: dict[str, set[str]] = {}

    # --- 1. patterns under rules (both mapped in the Forest SSSOM) ---
    for fp in by_obj:
        if forest_object_kind(fp) != "pattern":
            continue
        fr = fp.rsplit("/", 1)[0]
        rule_homes = [h for h in chemist_sssom_homes(by_obj, fr) if h in concepts]
        if not rule_homes:
            continue
        rule_sub = rule_homes[0]
        for sub in chemist_sssom_homes(by_obj, fp):
            if sub in concepts and not under_or_equal(sub, rule_sub, pm, memo):
                findings.append(
                    Finding(
                        "forest_pattern_under_rule",
                        sub,
                        f"pattern subject not under rule concept {rule_sub} ({fr})",
                        fp,
                    )
                )

    # --- 2. rules under catalogs ---
    membership = load_rule_to_ruleset_membership()
    for fr, rs in sorted(membership.items()):
        # Conjugation catalog deferred until SSSOM row exists.
        if rs == "xf:Conjugation" and rs not in by_obj:
            continue
        rule_homes = [h for h in chemist_sssom_homes(by_obj, fr) if h in concepts]
        if not rule_homes:
            findings.append(
                Finding(
                    "forest_rule_under_ruleset",
                    fr,
                    f"rule has no chemist SSSOM home to check under {rs}",
                    rs,
                )
            )
            continue
        rs_homes = [h for h in chemist_sssom_homes(by_obj, rs) if h in concepts]
        if not rs_homes:
            findings.append(
                Finding(
                    "forest_rule_under_ruleset",
                    rule_homes[0],
                    f"catalog {rs} has no chemist SSSOM home",
                    fr,
                )
            )
            continue
        for rule_sub in rule_homes:
            if any(under_or_equal(rule_sub, rs_sub, pm, memo) for rs_sub in rs_homes):
                continue
            homes = ", ".join(rs_homes)
            findings.append(
                Finding(
                    "forest_rule_under_ruleset",
                    rule_sub,
                    f"rule subject not under catalog home(s) {homes} ({rs})",
                    fr,
                )
            )

    # --- 3. catalogs under required parents ---
    for rs, ancestor in RULESET_REQUIRED_ANCESTOR.items():
        homes = chemist_sssom_homes(by_obj, rs)
        if not homes:
            findings.append(
                Finding(
                    "forest_ruleset_nesting",
                    ancestor,
                    f"no chemist SSSOM home for {rs}",
                    rs,
                )
            )
            continue
        for sub in homes:
            if sub not in concepts:
                findings.append(
                    Finding(
                        "forest_ruleset_nesting",
                        sub,
                        "catalog SSSOM subject not in XMET",
                        rs,
                    )
                )
                continue
            if not under_or_equal(sub, ancestor, pm, memo):
                findings.append(
                    Finding(
                        "forest_ruleset_nesting",
                        sub,
                        f"catalog home not under {ancestor}",
                        rs,
                    )
                )

    # Conjugation: optional until catalog ships; when present, nest under conjugation + RC.
    cj_homes = chemist_sssom_homes(by_obj, "xf:Conjugation")
    if not cj_homes:
        return
    for sub in cj_homes:
        if sub not in concepts:
            findings.append(
                Finding(
                    "forest_ruleset_nesting",
                    sub,
                    "Conjugation catalog SSSOM subject not in XMET",
                    "xf:Conjugation",
                )
            )
            continue
        if not under_or_equal(sub, CONJUGATION, pm, memo):
            findings.append(
                Finding(
                    "forest_ruleset_nesting",
                    sub,
                    "Conjugation catalog home not under conjugation",
                    "xf:Conjugation",
                )
            )
        if not under_or_equal(sub, REACTION_CLASS, pm, memo):
            findings.append(
                Finding(
                    "forest_ruleset_nesting",
                    sub,
                    "Conjugation catalog home not under reaction class",
                    "xf:Conjugation",
                )
            )


def check_forest_phaseone(
    findings: list[Finding],
    concepts: dict[str, dict[str, Any]],
    pm: dict[str, list[str]],
) -> None:
    rows = load_sssom(FOREST_SSSOM)
    by_obj = index_sssom_by_object(rows)

    check_unique_sssom_homes(
        findings,
        rows,
        object_kind="pattern",
        check_id="forest_pattern_unique_home",
        label="Forest pattern",
    )
    # Multiple Forest patterns may share one chemical subject when they are
    # representation / encoding variants of the same chemistry. Still require
    # unique object→subject homes above.
    check_unique_sssom_subjects(
        findings,
        rows,
        object_kind="rule",
        check_id="forest_rule_unique_subject",
        label="Forest rule",
    )

    # Catalog / color mappings (long xf: names only — never SO/UO/…).
    # Dehydrogenation / Hydrolysis are rule exactMatch homes (ex-DH/HD catalogs).
    for catalog, xmet_id in [
        ("xf:StableOxygenation", SO),
        ("xf:UnstableOxygenation", UO),
        ("xf:Dehydrogenation", DH),
        ("xf:Hydrolysis", HD),
        ("xf:Reduction", RD),
    ]:
        if catalog not in by_obj:
            findings.append(
                Finding("forest_ruleset_mapped", xmet_id, f"no SSSOM row for {catalog}", catalog)
            )
        else:
            subs = {r["subject_id"] for r in by_obj[catalog]}
            if xmet_id not in subs and not any(s in concepts for s in subs):
                findings.append(
                    Finding(
                        "forest_ruleset_mapped",
                        xmet_id,
                        f"catalog {catalog} not linked from chemist color",
                        catalog,
                    )
                )

    # PhaseOneRS rules + patterns from draft inventory
    expected_rules: list[str] = []
    draft: dict[str, Any] = {}
    if DRAFT_PHASE1.exists():
        draft = json.loads(DRAFT_PHASE1.read_text())
        expected_rules = list(draft.get("phaseone_rules_in_forest") or [])

    for rule in expected_rules:
        obj = xf_rule(rule)
        if obj not in by_obj:
            findings.append(
                Finding(
                    "forest_phaseone_rule_coverage",
                    rule,
                    "PhaseOneRS rule missing SSSOM mapping",
                    obj,
                )
            )
            continue
        for r in by_obj[obj]:
            sub = r["subject_id"]
            if sub not in concepts:
                findings.append(
                    Finding(
                        "forest_sssom_subject_exists",
                        sub,
                        "Forest SSSOM subject_id not in XMET",
                        obj,
                    )
                )

    # Rule rows: exactMatch or closeMatch only (not relatedMatch).
    for obj, mapped in by_obj.items():
        if forest_object_kind(obj) != "rule":
            continue
        for r in mapped:
            pred = r.get("predicate_id") or ""
            if pred not in ALLOWED_RULE_PATTERN_PREDS:
                findings.append(
                    Finding(
                        "forest_rule_predicate",
                        r.get("subject_id") or obj,
                        f"xf: rule mapping must be exactMatch or closeMatch; got {pred}",
                        obj,
                    )
                )

    # Pattern rows: exactMatch or closeMatch
    for obj, mapped in by_obj.items():
        if forest_object_kind(obj) != "pattern":
            continue
        for r in mapped:
            pred = r.get("predicate_id") or ""
            if pred not in ALLOWED_RULE_PATTERN_PREDS:
                findings.append(
                    Finding(
                        "forest_pattern_predicate",
                        r.get("subject_id") or obj,
                        f"xf: pattern mapping must be exactMatch or closeMatch; got {pred}",
                        obj,
                    )
                )

    # Also keep draft PhaseOne pattern hierarchy checks when present.
    expected_patterns: list[tuple[str, str]] = []  # (xf:pattern, xf:rule)
    for color in (draft.get("reaction_class") or {}).get("phase_one_colors") or []:
        for rule in color.get("rules") or []:
            fr = normalize_forest_object(rule.get("forest_rule") or "")
            for pat in rule.get("patterns") or []:
                fp = normalize_forest_object(pat.get("forest_pattern") or "")
                if fp.startswith("xf:") and fr.startswith("xf:"):
                    expected_patterns.append((fp, fr))

    seen_fp: set[str] = set()
    for fp, fr in expected_patterns:
        if fp in seen_fp:
            continue
        seen_fp.add(fp)
        rows_for = by_obj.get(fp) or []
        if not rows_for:
            findings.append(
                Finding(
                    "forest_phaseone_pattern_coverage",
                    fp,
                    "Forest pattern missing SSSOM mapping",
                    fp,
                )
            )
            continue
        chemist_rows = [r for r in rows_for if not r["subject_id"].startswith("xmet:9")]
        if not chemist_rows:
            alias = rows_for[0]["subject_id"]
            findings.append(
                Finding(
                    "forest_pattern_chemist_subject",
                    fp,
                    f"pattern mapped only via forest-map alias ({alias}); needs chemist exactMatch home",
                    alias,
                )
            )
            continue
        for r in chemist_rows:
            sub = r["subject_id"]
            if sub not in concepts:
                findings.append(
                    Finding(
                        "forest_sssom_subject_exists",
                        sub,
                        "Forest SSSOM subject_id not in XMET",
                        fp,
                    )
                )
                continue
            pred = r.get("predicate_id") or ""
            if pred not in ALLOWED_RULE_PATTERN_PREDS:
                findings.append(
                    Finding(
                        "forest_pattern_exact_match",
                        sub,
                        f"pattern conceptual home must be exactMatch or closeMatch; got {pred}",
                        fp,
                    )
                )

    # Conjugation catalog should not map only to phase II tag
    for r in by_obj.get("xf:Conjugation", []):
        if r["subject_id"] in PHASE_TAGS:
            findings.append(
                Finding(
                    "forest_cj_fork",
                    r["subject_id"],
                    "Conjugation catalog should map to conjugation / fork, not disposition phase tag",
                    "xf:Conjugation",
                )
            )

    # GSH mapping subject under adducts
    for r in rows:
        if r["object_id"] == "xf:Glutathionation":
            sub = r["subject_id"]
            if sub in concepts:
                anc = ancestors(sub, pm) | set(pm.get(sub, []))
                if ADDUCT not in anc and sub != ADDUCT:
                    findings.append(
                        Finding(
                            "forest_gsh_adduct_fork",
                            sub,
                            "Glutathionation mapping subject not under adduct formation",
                            r["object_id"],
                        )
                    )


def check_related_match_discipline(
    findings: list[Finding],
    concepts: dict[str, dict[str, Any]],
) -> None:
    """relatedMatch is disallowed except Forest catalog SSSOM rows (``xf:``).

    YAML ``related_match`` and non-catalog SSSOM relatedMatch must be curated
    away; antonyms use ``antonyms:`` / ``xmet:antonymOf`` instead.
    """
    for cid, c in concepts.items():
        if c.get("related_match"):
            findings.append(
                Finding(
                    "yaml_related_match_forbidden",
                    cid,
                    "YAML related_match is not allowed; use antonyms/has_part/parents or drop",
                )
            )

    for path in (FOREST_SSSOM, EXTERNAL_SSSOM, MOP_SSSOM, MESH_SSSOM, TAGGER_SSSOM):
        for r in load_sssom(path):
            if r.get("predicate_id") != "skos:relatedMatch":
                continue
            obj = r.get("object_id") or ""
            if path.resolve() == FOREST_SSSOM.resolve() and is_relatedmatch_catalog(obj):
                continue
            # Legacy forest.ruleset:* still accepted if present during transition.
            if obj.startswith("forest.ruleset:"):
                continue
            findings.append(
                Finding(
                    "sssom_related_match_forbidden",
                    r.get("subject_id") or "",
                    "relatedMatch not allowed except Forest catalog xf:* "
                    "(PhaseOne/StableOxygenation/UnstableOxygenation/Reduction/Conjugation) "
                    f"(file {path.name})",
                    obj,
                )
            )


def load_renumber_old_ids() -> dict[str, str]:
    """new_id → old_id from the opaque renumber cut (if present)."""
    path = ROOT / "data/mappings/xmet-id-renumber.tsv"
    if not path.exists():
        return {}
    out: dict[str, str] = {}
    with path.open() as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            old = (row.get("old_id") or "").strip()
            new = (row.get("new_id") or "").strip()
            if old and new:
                out[new] = old
    return out


def check_external_exact_discipline(findings: list[Finding]) -> None:
    """Soft external matches forbidden on concepts that were redesign-era mints.

    After the opaque ``4000000+`` renumber, detect redesign-era origins via
    ``xmet-id-renumber.tsv`` (old ``xmet:3xxxxxx``). Legacy homes that merely
    moved into the 4-block keep their closeMatch/broadMatch rows.
    """
    new_to_old = load_renumber_old_ids()

    def is_redesign_era(sub: str) -> bool:
        if sub.startswith("xmet:3"):
            return True
        old = new_to_old.get(sub, "")
        return old.startswith("xmet:3")

    for path in (EXTERNAL_SSSOM, MOP_SSSOM, MESH_SSSOM):
        for r in load_sssom(path):
            sub = r["subject_id"]
            if not is_redesign_era(sub):
                continue
            if r["predicate_id"] != "skos:exactMatch":
                findings.append(
                    Finding(
                        "external_exact_only",
                        sub,
                        f"non-exact external mapping for redesign-era id ({r['predicate_id']})",
                        r["object_id"],
                    )
                )


def check_tagger_sssom(
    findings: list[Finding],
    concepts: dict[str, dict[str, Any]],
    pm: dict[str, list[str]],
) -> None:
    """Every tagger SSSOM exactMatch home exists and sits under reaction class."""
    rows = load_sssom(TAGGER_SSSOM)
    check_unique_sssom_homes(
        findings,
        rows,
        object_prefix="rule:",
        check_id="tagger_smarts_unique_home",
        label="tagger SMARTS rule",
    )
    # Multiple tagger detectors (OH-only vs OH/O−, mapped vs unmapped, …) may
    # share one chemical subject. Object→subject uniqueness still enforced.

    memo: dict[str, set[str]] = {}
    for r in rows:
        if r.get("predicate_id") != "skos:exactMatch":
            continue
        sub, rid = r["subject_id"], r["object_id"]
        if sub not in concepts:
            findings.append(
                Finding("tagger_sssom_subject_exists", sub, "tagger SSSOM subject not in live ontology", rid)
            )
        elif sub != REACTION_CLASS and REACTION_CLASS not in ancestors(sub, pm, memo):
            findings.append(
                Finding(
                    "tagger_smarts_reaction_class",
                    sub,
                    "tagger SMARTS exactMatch subject not under reaction class",
                    rid,
                )
            )


def run() -> int:
    data = load_yaml()
    concepts = by_id(data)
    pm = parents_map(data)
    findings: list[Finding] = []

    check_remap(findings, concepts)
    check_disposition_not_chem_parent(findings, pm)
    check_single_parent(findings, concepts)
    check_five_colors_and_conjugation(findings, concepts, pm)
    check_descriptor_orthogonal(findings, concepts, pm)
    check_relation_vocab(findings, concepts)
    check_definition_no_product_refs(findings, concepts)
    check_redundant_soft_targets(findings, concepts, pm)
    check_forest_phaseone(findings, concepts, pm)
    check_forest_nesting(findings, concepts, pm)
    check_dealkylation_pattern_always_with(findings, concepts, pm)
    check_tagger_sssom(findings, concepts, pm)
    check_related_match_discipline(findings, concepts)
    check_external_exact_discipline(findings)

    xfail = load_xfail()
    hard: list[Finding] = []
    xf: list[Finding] = []
    for f in findings:
        if f.key() in xfail or (f.check_id, f.subject_id, "") in xfail:
            xf.append(f)
        else:
            hard.append(f)

    print(f"findings: {len(findings)}  hard: {len(hard)}  xfail: {len(xf)}")
    for f in xf:
        print(f"XFAIL {f}")
    # Coverage guide: group hard failures by check_id (do not auto-fix).
    by_check: dict[str, list[Finding]] = defaultdict(list)
    for f in hard:
        by_check[f.check_id].append(f)
    for check_id in sorted(by_check):
        group = by_check[check_id]
        print(f"\n== {check_id} ({len(group)}) ==")
        for f in group:
            print(f"FAIL  {f}")
    return 1 if hard else 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    raise SystemExit(run())


if __name__ == "__main__":
    main()
