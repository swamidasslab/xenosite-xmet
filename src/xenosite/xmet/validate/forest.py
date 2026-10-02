"""Checks of a Metabolic Forest checkout (``rules.rs``) against XMET's Forest SSSOM.

Run from the Forest repository to confirm that every live rule pattern has a
chemist home in XMET and that no SSSOM row points at a pattern Forest removed.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from xenosite.xmet.validate import core
from xenosite.xmet.validate.core import Finding

ALLOWED_PREDICATES = core.ALLOWED_RULE_PATTERN_PREDS


FN_RE = re.compile(r"^(?:pub(?:\([^)]*\))?\s+)?fn\s+(\w+)\s*[<(]", re.M)
PATTERN_RE = re.compile(r'(?:smirks_row|endpoint_row|PatternInfo::[a-z_]+)\(\s*"([^"]+)"')
CALL_RE = re.compile(r"\b([a-z_][a-z0-9_]*)\s*\(")
LEAF_NAME_RES = (
    re.compile(r'RuleSet::new\(\s*Some\("([^"]+)"'),
    re.compile(r'\b[a-z_]+_leaf\(\s*"([^"]+)"'),
)
COMPOSE_NAME_RE = re.compile(r'RuleSet::compose\(\s*Some\("([^"]+)"')


def _block_end(text: str, pos: int) -> int:
    """Index just past the ``{…}`` block that starts at or after ``pos`` (string literals skipped)."""
    i = text.find("{", pos)
    if i < 0:
        return len(text)
    depth, n = 0, len(text)
    while i < n:
        ch = text[i]
        if ch == '"':
            i += 1
            while i < n and text[i] != '"':
                i += 2 if text[i] == "\\" else 1
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    return n


class RulesSource:
    """Static read of Forest ``rules.rs``: leaf rules, their patterns, and catalogs.

    Functions are split at every ``fn`` (public or private) and helper calls are
    followed, so patterns built in shared helpers (``glutathionation_patterns``)
    and leaves built through wrappers (``reactivity_leaf("GSH", …)``) resolve to
    the right rule. Conditionals are not evaluated: a helper's patterns count
    for every leaf that calls it.
    """

    def __init__(self, text: str) -> None:
        self.bodies: dict[str, str] = {}
        for m in FN_RE.finditer(text):
            self.bodies.setdefault(m.group(1), text[m.start() : _block_end(text, m.end())])
        self.leaves: dict[str, str] = {}  # fn name → rule name
        self.catalogs: dict[str, str] = {}  # fn name → catalog name
        for fn, body in self.bodies.items():
            if "-> RuleSet" not in body.split("{", 1)[0]:
                continue
            compose = COMPOSE_NAME_RE.search(body)
            if compose:
                self.catalogs[fn] = compose.group(1)
                continue
            for rx in LEAF_NAME_RES:
                m = rx.search(body)
                if m:
                    self.leaves[fn] = m.group(1)
                    break

    def calls(self, fn: str) -> list[str]:
        body = self.bodies[fn].split("{", 1)[-1]
        return [c for c in dict.fromkeys(CALL_RE.findall(body)) if c in self.bodies and c != fn]

    def patterns(self, fn: str, seen: frozenset[str] = frozenset()) -> list[str]:
        out = PATTERN_RE.findall(self.bodies[fn])
        for c in self.calls(fn):
            if c not in seen and c not in self.catalogs:
                out += self.patterns(c, seen | {fn})
        return list(dict.fromkeys(out))

    def members(self, fn: str, seen: frozenset[str] = frozenset()) -> list[str]:
        """Leaf rule names reachable from a catalog function."""
        out: list[str] = []
        for c in self.calls(fn):
            if c in self.leaves:
                out.append(self.leaves[c])
            elif c not in seen:
                out += self.members(c, seen | {fn})
        return list(dict.fromkeys(out))


def load_catalog_patterns(rules_rs: Path) -> dict[str, list[str]]:
    """Leaf rule name → pattern names from Forest ``rules.rs``."""
    src = RulesSource(rules_rs.read_text())
    return {name: src.patterns(fn) for fn, name in src.leaves.items()}


def load_compose_members(rules_rs: Path) -> dict[str, list[str]]:
    """Catalog name (PhaseOne, Reactivity, …) → leaf rule names it composes."""
    src = RulesSource(rules_rs.read_text())
    return {name: src.members(fn) for fn, name in src.catalogs.items()}


def check_catalog_parsed(findings: list[Finding], catalog: dict[str, list[str]], rules_rs: Path) -> None:
    if not catalog:
        findings.append(
            Finding("forest_catalog_patterns_present", "xmet:4000213", f"no Forest leaf patterns parsed from {rules_rs}")
        )


def check_pattern_coverage(
    findings: list[Finding],
    catalog: dict[str, list[str]],
    by_obj: dict[str, list[dict[str, str]]],
    concepts: dict[str, dict[str, Any]],
) -> None:
    """Every live Forest pattern has a chemist (non-alias) home mapped by exact/closeMatch."""
    for rule_name, pats in catalog.items():
        for pname in pats:
            fp = f"xf:{rule_name}/{pname}"
            rows = by_obj.get(fp) or []
            if not rows:
                findings.append(Finding("forest_pattern_coverage", fp, "Forest pattern missing SSSOM mapping", fp))
                continue
            chemist = [r for r in rows if not r["subject_id"].startswith("xmet:9")]
            if not chemist:
                findings.append(
                    Finding(
                        "forest_pattern_chemist_subject",
                        fp,
                        f"pattern mapped only via forest-map alias ({rows[0]['subject_id']}); needs chemist home",
                        rows[0]["subject_id"],
                    )
                )
            for r in chemist:
                if r["subject_id"] not in concepts:
                    findings.append(
                        Finding("forest_sssom_subject_exists", r["subject_id"], "Forest SSSOM subject_id not in XMET", fp)
                    )
                elif (r.get("predicate_id") or "") not in ALLOWED_PREDICATES:
                    findings.append(
                        Finding(
                            "forest_pattern_exact_match",
                            r["subject_id"],
                            f"pattern home must be exactMatch or closeMatch; got {r.get('predicate_id')}",
                            fp,
                        )
                    )


def check_pattern_orphans(
    findings: list[Finding],
    catalog: dict[str, list[str]],
    by_obj: dict[str, list[dict[str, str]]],
) -> None:
    """SSSOM pattern rows whose pattern no longer exists in the live Forest catalog."""
    live = {f"xf:{rule}/{p}" for rule, pats in catalog.items() for p in pats}
    for obj, rows in by_obj.items():
        if core.forest_object_kind(obj) == "pattern" and obj not in live:
            findings.append(
                Finding("forest_pattern_sssom_orphan", rows[0]["subject_id"], "SSSOM xf: pattern not in live Forest catalog", obj)
            )


def check_phaseone_leaves(
    findings: list[Finding],
    compose: dict[str, list[str]],
    by_obj: dict[str, list[dict[str, str]]],
    concepts: dict[str, dict[str, Any]],
    pm: dict[str, list[str]],
) -> None:
    """PhaseOne catalog leaves without a colour/conjugation membership nest under reaction class."""
    colored = set(core.load_rule_to_ruleset_membership())
    memo: dict[str, set[str]] = {}
    for rule_name in compose.get("PhaseOne") or []:
        fr = f"xf:{rule_name}"
        if fr in colored:
            continue
        for sub in core.chemist_sssom_homes(by_obj, fr):
            if sub in concepts and not core.under_or_equal(sub, core.REACTION_CLASS, pm, memo):
                findings.append(
                    Finding(
                        "forest_rule_under_ruleset",
                        sub,
                        "PhaseOne leaf without color membership not under reaction class",
                        fr,
                    )
                )


def forest_findings(rules_rs: Path) -> list[Finding]:
    """All Forest-catalog checks for one ``rules.rs``."""
    data = core.load_yaml()
    concepts = core.by_id(data)
    pm = core.parents_map(data)
    by_obj = core.index_sssom_by_object(core.load_sssom(core.FOREST_SSSOM))
    catalog = load_catalog_patterns(rules_rs)
    findings: list[Finding] = []
    check_catalog_parsed(findings, catalog, rules_rs)
    check_pattern_coverage(findings, catalog, by_obj, concepts)
    check_pattern_orphans(findings, catalog, by_obj)
    check_phaseone_leaves(findings, load_compose_members(rules_rs), by_obj, concepts, pm)
    return findings
