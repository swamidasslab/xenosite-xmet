#!/usr/bin/env python3
"""Validate XMET redesign v1 locked goals.

Hard failures unless listed in data/mappings/validation-xfail.tsv.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
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
DEFAULT_TAGGER_RULES_DIR = ROOT.parent / "crates" / "xenosite-tagger" / "data" / "rules"
DEFAULT_FOREST_RULES_RS = ROOT.parent / "crates" / "xenosite-forest" / "src" / "rules.rs"
TAGGER_RULE_FILES = ("xenobiotic.rules.yaml", "structural.rules.yaml")
ALLOWED_RULE_PATTERN_PREDS = {"skos:exactMatch", "skos:closeMatch"}

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

# Color / conjugation membership beyond draft PhaseOne colors (specialized leaves).
EXTRA_RULE_TO_RULESET: dict[str, str] = {
    "NDealkylation": "forest.ruleset:UO",
    "AzoSplitting": "forest.ruleset:RD",
    "BenzodioxoleReduction": "forest.ruleset:RD",
    "NitroaromaticReduction": "forest.ruleset:RD",
    "ThiopheneSulfurOxidation": "forest.ruleset:SO",
}
CJ_RULES = ("Acetylation", "Sulfation", "Glucuronidation", "Glutathionation")

# Rules whose Forest color membership is operational only — chemical parent may
# differ (no multi-inheritance). Nesting under the ruleset home is not required.
OPERATIONAL_RULESET_MEMBERSHIP_ONLY = {
    "forest.rule:Dehydration",  # chemically elimination / isoredox; Forest lists under RD
    "forest.rule:EpoxideOpening",  # chemically isoredox ring opening; Forest lists under HD
}

# Closest chemist parent each Forest ruleset home must nest under (or equal).
RULESET_REQUIRED_ANCESTOR: dict[str, str] = {
    "forest.ruleset:SO": OXIDATION,
    "forest.ruleset:UO": OXIDATION,
    "forest.ruleset:DH": OXIDATION,
    "forest.ruleset:HD": ISOREDOX,
    "forest.ruleset:RD": REACTION_CLASS,
    "forest.ruleset:PhaseOne": DISPOSITION,
}


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
        return list(reader)


def forest_rules_rs() -> Path | None:
    override = os.environ.get("XMET_FOREST_RULES_RS")
    path = Path(override) if override else DEFAULT_FOREST_RULES_RS
    return path if path.is_file() else None


def load_forest_catalog_patterns(rules_rs: Path) -> dict[str, list[str]]:
    """Parse live Forest leaf RuleSet → pattern names from rules.rs.

    Pattern names are the first string argument of ``smirks_row`` /
    ``endpoint_row`` / ``PatternInfo::<ctor>`` inside each
    ``pub fn …() -> RuleSet`` leaf (skips phase_one / default / all catalogs).
    """
    text = rules_rs.read_text()
    parts = re.split(r"\n(?=pub fn [a-z_]+\(\) -> RuleSet)", text)
    catalog: dict[str, list[str]] = {}
    skip = {"phase_one", "default_ruleset", "all_rules"}
    for part in parts:
        m = re.match(r"pub fn ([a-z_]+)\(\) -> RuleSet", part)
        if not m or m.group(1) in skip:
            continue
        nm = re.search(r'RuleSet::new\(\s*Some\("([^"]+)"', part)
        if not nm:
            continue
        rule = nm.group(1)
        pats: list[str] = []
        for helper in ("smirks_row", "endpoint_row"):
            pats.extend(re.findall(rf'{helper}\(\s*"([^"]+)"', part))
        pats.extend(re.findall(r'PatternInfo::[a-z_]+\(\s*"([^"]+)"', part))
        seen: set[str] = set()
        uniq: list[str] = []
        for p in pats:
            if p not in seen:
                seen.add(p)
                uniq.append(p)
        catalog[rule] = uniq
    return catalog


def load_forest_compose_members(rules_rs: Path) -> dict[str, list[str]]:
    """Parse ``RuleSet::compose`` catalogs → leaf rule names (PascalCase).

    Maps catalog name (PhaseOne, Default, All) to ordered leaf rule names.
    """
    text = rules_rs.read_text()
    # fn snake → RuleSet::new Some("Pascal") for leaf lookup
    snake_to_pascal: dict[str, str] = {}
    for m in re.finditer(
        r'pub fn ([a-z_]+)\(\) -> RuleSet \{[\s\S]*?RuleSet::new\(\s*Some\("([^"]+)"',
        text,
    ):
        snake_to_pascal[m.group(1)] = m.group(2)

    catalogs: dict[str, list[str]] = {}
    for m in re.finditer(
        r"pub fn ([a-z_]+)\(\) -> RuleSet \{\s*RuleSet::compose\(\s*Some\(\"([^\"]+)\"",
        text,
    ):
        fn_name, catalog_name = m.group(1), m.group(2)
        # Body until matching close of compose — take until next pub fn or end
        start = m.end()
        nxt = re.search(r"\npub fn ", text[start:])
        body = text[start : start + nxt.start()] if nxt else text[start:]
        members: list[str] = []
        for call in re.findall(r"\b([a-z_]+)\(\)", body):
            if call in {"compose", "into", "from"}:
                continue
            pascal = snake_to_pascal.get(call)
            if pascal:
                members.append(pascal)
        catalogs[catalog_name] = members
    return catalogs


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
    """forest.rule:Name → forest.ruleset:… from draft colors + curated extras + CJ."""
    membership: dict[str, str] = {}
    if DRAFT_PHASE1.exists():
        draft = json.loads(DRAFT_PHASE1.read_text())
        for color in (draft.get("reaction_class") or {}).get("phase_one_colors") or []:
            rs = color.get("forest_ruleset") or ""
            for rule in color.get("rules") or []:
                fr = rule.get("forest_rule") or ""
                if fr and rs:
                    membership[fr] = rs
    for rule_name, rs in EXTRA_RULE_TO_RULESET.items():
        membership.setdefault(f"forest.rule:{rule_name}", rs)
    for rule_name in CJ_RULES:
        membership.setdefault(f"forest.rule:{rule_name}", "forest.ruleset:CJ")
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
    object_prefix: str,
    check_id: str,
    label: str,
) -> None:
    """Each Forest/tagger object may have only one XMET home (object → subject)."""
    by_obj: dict[str, list[dict[str, str]]] = defaultdict(list)
    for r in rows:
        obj = r.get("object_id") or ""
        if obj.startswith(object_prefix):
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
    object_prefix: str,
    check_id: str,
    label: str,
) -> None:
    """Each XMET home may map to at most one object in a peer class (subject → object).

    Peer classes: forest.pattern↔forest.pattern, forest.rule↔forest.rule,
    tagger rule:↔rule:. Cross-class co-homes (pattern+rule on one concept) are OK.
    """
    by_sub: dict[str, list[str]] = defaultdict(list)
    for r in rows:
        obj = r.get("object_id") or ""
        if not obj.startswith(object_prefix):
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

    Parent covers descendants; enumerating children is redundant fan-out
    (e.g. halide LG → oxidative dehalogenation already covers ox-dehal leaves).
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


def check_dealkylation_pattern_always_with(
    findings: list[Finding],
    concepts: dict[str, dict[str, Any]],
    pm: dict[str, list[str]],
) -> None:
    """Dealkylation / N-dealkylation patterns may share a site home iff alwaysWith distinguishes them.

    Policy for ``forest.pattern:Dealkylation/*`` and ``forest.pattern:NDealkylation/*``:
    - Every such SSSOM row must list ``always_with`` descriptor CURIEs (pipe-separated)
      under reaction descriptor.
    - Patterns that share the same subject_id must have distinct always_with sets.
    """
    rows = load_sssom(FOREST_SSSOM)
    prefixes = ("forest.pattern:Dealkylation/", "forest.pattern:NDealkylation/")
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
        seen: dict[frozenset[str], str] = {}
        for r in group:
            obj = r.get("object_id") or ""
            aw = frozenset(
                x.strip() for x in (r.get("always_with") or "").split("|") if x.strip()
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
    """Forest hierarchy mirrored in XMET: pattern ⊂ rule ⊂ ruleset ⊂ parent.

    1. Every live ``forest.pattern:Rule/pat`` chemist home nests under the
       mapped ``forest.rule:Rule`` chemist home.
    2. Every rule with a known ruleset membership nests under (or equals) at
       least one chemist home of that ruleset.
    3. Every ruleset chemist home nests under its required reaction-class /
       disposition ancestor; CJ homes nest under conjugation (or are it).
    """
    rows = load_sssom(FOREST_SSSOM)
    by_obj: dict[str, list[dict[str, str]]] = defaultdict(list)
    for r in rows:
        by_obj[r["object_id"]].append(r)

    memo: dict[str, set[str]] = {}

    # --- 1. patterns under rules (live Forest catalog) ---
    rules_rs = forest_rules_rs()
    catalog: dict[str, list[str]] = load_forest_catalog_patterns(rules_rs) if rules_rs else {}
    for rule_name, pats in catalog.items():
        fr = f"forest.rule:{rule_name}"
        rule_homes = [h for h in chemist_sssom_homes(by_obj, fr) if h in concepts]
        if not rule_homes:
            continue
        rule_sub = rule_homes[0]
        for pname in pats:
            fp = f"forest.pattern:{rule_name}/{pname}"
            for sub in chemist_sssom_homes(by_obj, fp):
                if sub not in concepts:
                    continue
                if not under_or_equal(sub, rule_sub, pm, memo):
                    findings.append(
                        Finding(
                            "forest_pattern_under_rule",
                            sub,
                            f"pattern subject not under rule concept {rule_sub} ({fr})",
                            fp,
                        )
                    )

    # --- 2. rules under rulesets ---
    membership = load_rule_to_ruleset_membership()
    for fr, rs in sorted(membership.items()):
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
                    f"ruleset {rs} has no chemist SSSOM home",
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
                    f"rule subject not under ruleset home(s) {homes} ({rs})",
                    fr,
                )
            )

    # PhaseOne catalog leaves without a color/CJ membership still nest under RC.
    if rules_rs:
        compose = load_forest_compose_members(rules_rs)
        colored = set(membership)
        for rule_name in compose.get("PhaseOne") or []:
            fr = f"forest.rule:{rule_name}"
            if fr in colored:
                continue
            for rule_sub in chemist_sssom_homes(by_obj, fr):
                if rule_sub not in concepts:
                    continue
                if not under_or_equal(rule_sub, REACTION_CLASS, pm, memo):
                    findings.append(
                        Finding(
                            "forest_rule_under_ruleset",
                            rule_sub,
                            "PhaseOne leaf without color membership not under reaction class",
                            fr,
                        )
                    )

    # --- 3. rulesets under required parents ---
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
                        "ruleset SSSOM subject not in XMET",
                        rs,
                    )
                )
                continue
            if not under_or_equal(sub, ancestor, pm, memo):
                findings.append(
                    Finding(
                        "forest_ruleset_nesting",
                        sub,
                        f"ruleset home not under {ancestor}",
                        rs,
                    )
                )

    # CJ: each home is conjugation or nests under it; conjugation under RC.
    cj_homes = chemist_sssom_homes(by_obj, "forest.ruleset:CJ")
    if not cj_homes:
        findings.append(
            Finding(
                "forest_ruleset_nesting",
                CONJUGATION,
                "no chemist SSSOM home for forest.ruleset:CJ",
                "forest.ruleset:CJ",
            )
        )
    for sub in cj_homes:
        if sub not in concepts:
            findings.append(
                Finding(
                    "forest_ruleset_nesting",
                    sub,
                    "CJ ruleset SSSOM subject not in XMET",
                    "forest.ruleset:CJ",
                )
            )
            continue
        if not under_or_equal(sub, CONJUGATION, pm, memo):
            findings.append(
                Finding(
                    "forest_ruleset_nesting",
                    sub,
                    "CJ ruleset home not under conjugation",
                    "forest.ruleset:CJ",
                )
            )
        if not under_or_equal(sub, REACTION_CLASS, pm, memo):
            findings.append(
                Finding(
                    "forest_ruleset_nesting",
                    sub,
                    "CJ ruleset home not under reaction class",
                    "forest.ruleset:CJ",
                )
            )


def check_forest_phaseone(
    findings: list[Finding],
    concepts: dict[str, dict[str, Any]],
    pm: dict[str, list[str]],
) -> None:
    rows = load_sssom(FOREST_SSSOM)
    by_obj: dict[str, list[dict[str, str]]] = defaultdict(list)
    for r in rows:
        by_obj[r["object_id"]].append(r)

    check_unique_sssom_homes(
        findings,
        rows,
        object_prefix="forest.pattern:",
        check_id="forest_pattern_unique_home",
        label="Forest pattern",
    )
    # Multiple Forest patterns may share one chemical subject when they are
    # representation / encoding variants of the same chemistry. Still require
    # unique object→subject homes above.
    check_unique_sssom_subjects(
        findings,
        rows,
        object_prefix="forest.rule:",
        check_id="forest_rule_unique_subject",
        label="Forest rule",
    )

    for ruleset, xmet_id in [
        ("forest.ruleset:SO", SO),
        ("forest.ruleset:UO", UO),
        ("forest.ruleset:DH", DH),
        ("forest.ruleset:HD", HD),
        ("forest.ruleset:RD", RD),
    ]:
        if ruleset not in by_obj:
            findings.append(
                Finding("forest_ruleset_mapped", xmet_id, f"no SSSOM row for {ruleset}", ruleset)
            )
        else:
            subs = {r["subject_id"] for r in by_obj[ruleset]}
            if xmet_id not in subs and not any(s in concepts for s in subs):
                findings.append(
                    Finding(
                        "forest_ruleset_mapped",
                        xmet_id,
                        f"ruleset {ruleset} not linked from chemist color",
                        ruleset,
                    )
                )

    # PhaseOneRS rules + patterns from draft inventory
    expected_rules: list[str] = []
    draft: dict[str, Any] = {}
    if DRAFT_PHASE1.exists():
        draft = json.loads(DRAFT_PHASE1.read_text())
        expected_rules = list(draft.get("phaseone_rules_in_forest") or [])

    for rule in expected_rules:
        obj = f"forest.rule:{rule}"
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

    # forest.rule rows: exactMatch or closeMatch only (not relatedMatch)
    for obj, mapped in by_obj.items():
        if not obj.startswith("forest.rule:"):
            continue
        for r in mapped:
            pred = r.get("predicate_id") or ""
            if pred not in ALLOWED_RULE_PATTERN_PREDS:
                findings.append(
                    Finding(
                        "forest_rule_predicate",
                        r.get("subject_id") or obj,
                        f"forest.rule mapping must be exactMatch or closeMatch; got {pred}",
                        obj,
                    )
                )

    # forest.pattern rows (all, incl. conjugation): exactMatch or closeMatch
    for obj, mapped in by_obj.items():
        if not obj.startswith("forest.pattern:"):
            continue
        for r in mapped:
            pred = r.get("predicate_id") or ""
            if pred not in ALLOWED_RULE_PATTERN_PREDS:
                findings.append(
                    Finding(
                        "forest_pattern_predicate",
                        r.get("subject_id") or obj,
                        f"forest.pattern mapping must be exactMatch or closeMatch; got {pred}",
                        obj,
                    )
                )

    # Live Forest catalog: every leaf pattern must have a chemist SSSOM home.
    rules_rs = forest_rules_rs()
    if rules_rs is None:
        findings.append(
            Finding(
                "forest_rules_rs",
                "xmet:4000213",
                "Forest rules.rs not found (set XMET_FOREST_RULES_RS or keep sibling crate)",
            )
        )
        catalog: dict[str, list[str]] = {}
    else:
        catalog = load_forest_catalog_patterns(rules_rs)
        if not catalog:
            findings.append(
                Finding(
                    "forest_catalog_patterns_present",
                    "xmet:4000213",
                    f"no Forest leaf patterns parsed from {rules_rs}",
                )
            )

    # Also keep draft PhaseOne pattern hierarchy checks when present.
    expected_patterns: list[tuple[str, str]] = []  # (forest.pattern, forest.rule)
    for color in (draft.get("reaction_class") or {}).get("phase_one_colors") or []:
        for rule in color.get("rules") or []:
            fr = rule.get("forest_rule") or ""
            for pat in rule.get("patterns") or []:
                fp = pat.get("forest_pattern") or ""
                if fp and fr:
                    expected_patterns.append((fp, fr))

    live_fps: set[str] = set()
    for rule_name, pats in catalog.items():
        fr = f"forest.rule:{rule_name}"
        for pname in pats:
            fp = f"forest.pattern:{rule_name}/{pname}"
            live_fps.add(fp)
            expected_patterns.append((fp, fr))

    seen_fp: set[str] = set()
    for fp, fr in expected_patterns:
        if fp in seen_fp:
            continue
        seen_fp.add(fp)
        rows_for = by_obj.get(fp) or []
        if not rows_for:
            check = (
                "forest_pattern_coverage"
                if fp in live_fps
                else "forest_phaseone_pattern_coverage"
            )
            findings.append(
                Finding(
                    check,
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

    # Orphan pattern SSSOM rows (removed from Forest catalog)
    if catalog:
        for obj in by_obj:
            if obj.startswith("forest.pattern:") and obj not in live_fps:
                findings.append(
                    Finding(
                        "forest_pattern_sssom_orphan",
                        by_obj[obj][0]["subject_id"],
                        "SSSOM forest.pattern not in live Forest catalog",
                        obj,
                    )
                )

    # CJ should not map only to phase II tag
    for r in by_obj.get("forest.ruleset:CJ", []):
        if r["subject_id"] in PHASE_TAGS:
            findings.append(
                Finding(
                    "forest_cj_fork",
                    r["subject_id"],
                    "CJ ruleset should map to conjugation / fork, not disposition phase tag",
                    "forest.ruleset:CJ",
                )
            )

    # GSH mapping subject under adducts
    for r in rows:
        if r["object_id"] == "forest.rule:Glutathionation":
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
    """relatedMatch is disallowed except Forest ruleset SSSOM rows.

    YAML ``related_match`` and non-ruleset SSSOM relatedMatch must be curated
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

    allowed_obj_prefix = "forest.ruleset:"
    for path in (FOREST_SSSOM, EXTERNAL_SSSOM, MOP_SSSOM, MESH_SSSOM, TAGGER_SSSOM):
        for r in load_sssom(path):
            if r.get("predicate_id") != "skos:relatedMatch":
                continue
            obj = r.get("object_id") or ""
            if obj.startswith(allowed_obj_prefix):
                continue
            findings.append(
                Finding(
                    "sssom_related_match_forbidden",
                    r.get("subject_id") or "",
                    f"relatedMatch not allowed except {allowed_obj_prefix}* "
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


def tagger_rules_dir() -> Path | None:
    override = os.environ.get("XMET_TAGGER_RULES_DIR")
    path = Path(override) if override else DEFAULT_TAGGER_RULES_DIR
    return path if path.is_dir() else None


def load_tagger_smarts_rule_ids(directory: Path) -> list[str]:
    ids: list[str] = []
    for name in TAGGER_RULE_FILES:
        path = directory / name
        if not path.exists():
            continue
        data = yaml.safe_load(path.read_text())
        for rule in data.get("rules") or []:
            if rule.get("reactant_smarts") or rule.get("product_smarts"):
                ids.append(rule["id"])
    return ids


def check_tagger_smarts(
    findings: list[Finding],
    concepts: dict[str, dict[str, Any]],
    pm: dict[str, list[str]],
) -> None:
    """Every tagger SMARTS rule has an exactMatch home under reaction class."""
    directory = tagger_rules_dir()
    if directory is None:
        findings.append(
            Finding(
                "tagger_rules_dir",
                "xmet:4000213",
                "tagger rules dir not found (set XMET_TAGGER_RULES_DIR or keep sibling crate)",
            )
        )
        return

    smarts_ids = load_tagger_smarts_rule_ids(directory)
    if not smarts_ids:
        findings.append(
            Finding(
                "tagger_smarts_present",
                "xmet:4000213",
                f"no SMARTS rules found under {directory}",
            )
        )
        return

    rows = load_sssom(TAGGER_SSSOM)
    by_obj: dict[str, list[dict[str, str]]] = defaultdict(list)
    for r in rows:
        by_obj[r["object_id"]].append(r)

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
    for rid in smarts_ids:
        mapped = by_obj.get(rid) or []
        exact = [r for r in mapped if r["predicate_id"] == "skos:exactMatch"]
        if not exact:
            findings.append(
                Finding(
                    "tagger_smarts_coverage",
                    "xmet:4000213",
                    "SMARTS rule missing exactMatch row in xmet-tagger.sssom.tsv",
                    rid,
                )
            )
            continue
        for r in exact:
            sub = r["subject_id"]
            if sub not in concepts:
                findings.append(
                    Finding(
                        "tagger_sssom_subject_exists",
                        sub,
                        "tagger SSSOM subject not in live ontology",
                        rid,
                    )
                )
                continue
            if sub != REACTION_CLASS and REACTION_CLASS not in ancestors(sub, pm, memo):
                findings.append(
                    Finding(
                        "tagger_smarts_reaction_class",
                        sub,
                        "tagger SMARTS exactMatch subject not under reaction class",
                        rid,
                    )
                )

    # Orphan SSSOM rows (rule removed from tagger YAML)
    live_rules = set(smarts_ids)
    for obj, mapped in by_obj.items():
        if obj.startswith("rule:") and obj not in live_rules:
            findings.append(
                Finding(
                    "tagger_sssom_orphan",
                    mapped[0]["subject_id"],
                    "SSSOM object not a current SMARTS rule",
                    obj,
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
    check_redundant_soft_targets(findings, concepts, pm)
    check_forest_phaseone(findings, concepts, pm)
    check_forest_nesting(findings, concepts, pm)
    check_dealkylation_pattern_always_with(findings, concepts, pm)
    check_tagger_smarts(findings, concepts, pm)
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
