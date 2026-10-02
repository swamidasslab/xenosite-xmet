"""Generic quality checks. Each check is enabled and tuned in the `quality.checks` config."""
from __future__ import annotations

import re
from collections import defaultdict
from typing import Any, Callable

from .model import Vocabulary

Flag = dict[str, Any]
# A check returns (slug, detail) or (slug, detail, extra) hits. Concepts referenced in a
# detail as [[slug]] become the flag's `refs`; `extra` may add e.g. the `term` at issue.
Hit = tuple[str, str] | tuple[str, str, dict[str, Any]]
Check = Callable[[Vocabulary, dict[str, Any]], list[Hit]]
REF_RE = re.compile(r"\[\[([^\]]+)\]\]")

CHECKS: dict[str, Check] = {}


def check(name: str) -> Callable[[Check], Check]:
    def register(fn: Check) -> Check:
        CHECKS[name] = fn
        return fn

    return register


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower())


@check("missing_definition")
def _missing_definition(v: Vocabulary, opts: dict[str, Any]) -> list[tuple[str, str]]:
    return [(s, "") for s, c in v.concepts.items() if not c["definition"].strip()]


def _branch_value(v: Vocabulary, slug: str, by_branch: dict[str, Any], default: Any) -> Any:
    """Value for the nearest configured branch at or above ``slug`` (keys are CURIEs)."""
    c = v.concepts[slug]
    for s in [slug, *reversed(c["ancestors"])]:
        if v.concepts[s]["curie"] in by_branch:
            return by_branch[v.concepts[s]["curie"]]
    return default


@check("short_definition")
def _short_definition(v: Vocabulary, opts: dict[str, Any]) -> list[tuple[str, str]]:
    default = int(opts.get("min_chars", 40))
    out = []
    for s, c in v.concepts.items():
        n = int(_branch_value(v, s, opts.get("min_chars_under") or {}, default))
        if 0 < len(c["definition"].strip()) < n:
            out.append((s, f"{len(c['definition'].strip())} characters (minimum {n})"))
    return out


@check("templated_definition")
def _templated_definition(v: Vocabulary, opts: dict[str, Any]) -> list[tuple[str, str]]:
    """Placeholder definitions: start with the concept's own label and a colon, or match
    a configured placeholder pattern."""
    pats = [re.compile(p) for p in opts.get("patterns") or []]
    out = []
    for s, c in v.concepts.items():
        d = c["definition"].strip()
        if norm(d).startswith(norm(c["label"]) + ":") or any(p.search(d) for p in pats):
            out.append((s, "placeholder text instead of a definition"))
    return out


@check("missing_synonyms")
def _missing_synonyms(v: Vocabulary, opts: dict[str, Any]) -> list[tuple[str, str]]:
    return [(s, "") for s, c in v.concepts.items() if not c["synonyms"]]


@check("duplicate_label")
def _duplicate_label(v: Vocabulary, opts: dict[str, Any]) -> list[tuple[str, str]]:
    owners: dict[str, set[str]] = defaultdict(set)
    for s, c in v.concepts.items():
        for lab in [c["label"], *c["synonyms"]]:
            owners[norm(str(lab))].add(s)
    out = []
    for lab, slugs in owners.items():
        if len(slugs) > 1:
            for s in slugs:
                others = sorted(slugs - {s})
                out.append((s, f"“{lab}” also used by " + ", ".join(f"[[{o}]]" for o in others), {"term": lab}))
    return out


@check("near_duplicate_label")
def _near_duplicate_label(v: Vocabulary, opts: dict[str, Any]) -> list[tuple[str, str]]:
    threshold = float(opts.get("threshold", 92))
    try:
        from rapidfuzz import fuzz

        def score(a: str, b: str) -> float:
            return fuzz.ratio(a, b)
    except ImportError:  # pragma: no cover - fallback without rapidfuzz
        from difflib import SequenceMatcher

        def score(a: str, b: str) -> float:
            return 100 * SequenceMatcher(None, a, b).ratio()

    affixes = tuple(opts.get("ignore_prefixes") or [])
    short = int(opts.get("ignore_tokens_up_to", 0))
    numeral = re.compile(r"^(?:\d+|[ivx]+)$")

    def tokens(label: str) -> list[str]:
        return [t for t in re.split(r"[\s\-]+", label) if t]

    def core(toks: list[str]) -> list[str]:
        return [t for t in toks if not numeral.match(t) and len(t) > short]

    def distinct_by_design(a: str, b: str) -> bool:
        """Labels that differ only by numerals (phase I / II), short qualifiers such as
        locants (N- / O-dealkylation), or a configured negating prefix on one word
        (stable / unstable) are intentionally different concepts."""
        ta, tb = core(tokens(a)), core(tokens(b))
        if ta == tb:
            return True
        if len(ta) != len(tb):
            return False
        diff = [(x, y) for x, y in zip(ta, tb) if x != y]
        return len(diff) == 1 and any(x == p + y or y == p + x for x, y in diff for p in affixes)

    items = [(s, norm(c["label"])) for s, c in v.concepts.items()]
    out = []
    for i, (s1, a) in enumerate(items):
        for s2, b in items[i + 1:]:
            if a != b and score(a, b) >= threshold and not distinct_by_design(a, b):
                out.append((s1, f"similar to [[{s2}]]"))
                out.append((s2, f"similar to [[{s1}]]"))
    return out


@check("dangling_reference")
def _dangling_reference(v: Vocabulary, opts: dict[str, Any]) -> list[tuple[str, str]]:
    def label(rel: str) -> str:
        return (v.cfg.relations.get(rel) or {}).get("label", rel)

    return [(s, f"{label(rel)} → {target} (not in vocabulary)") for s, rel, target in v.dangling]


@check("unreciprocated_relation")
def _unreciprocated_relation(v: Vocabulary, opts: dict[str, Any]) -> list[tuple[str, str]]:
    out = []
    for src, rels in v.outgoing.items():
        for key, targets in rels.items():
            rc = v.cfg.relations[key]
            back = key if rc.get("symmetric") else rc.get("inverse")
            if not back:
                continue
            back_label = v.cfg.relations[back].get("label", back)
            for t in targets:
                if src not in v.outgoing[t].get(back, []):
                    out.append((src, f"states “{rc.get('label', key)}” [[{t}]], which does not state “{back_label}” this concept"))
    return out


@check("single_child")
def _single_child(v: Vocabulary, opts: dict[str, Any]) -> list[tuple[str, str]]:
    return [
        (s, f"only child: [[{c['children'][0]}]]")
        for s, c in v.concepts.items()
        if len(c["children"]) == 1
    ]


@check("wide_node")
def _wide_node(v: Vocabulary, opts: dict[str, Any]) -> list[tuple[str, str]]:
    n = int(opts.get("max_children", 15))
    return [
        (s, f"{len(c['children'])} children (guide: ≤ {n})")
        for s, c in v.concepts.items()
        if len(c["children"]) > n
    ]


@check("deep_node")
def _deep_node(v: Vocabulary, opts: dict[str, Any]) -> list[tuple[str, str]]:
    n = int(opts.get("max_depth", 8))
    return [(s, f"depth {c['depth']} (guide: ≤ {n})") for s, c in v.concepts.items() if c["depth"] > n]


@check("hierarchy_cycle")
def _hierarchy_cycle(v: Vocabulary, opts: dict[str, Any]) -> list[tuple[str, str]]:
    return [(s, "parent chain loops back on itself") for s in v.cycles]


@check("definition_forbidden_terms")
def _definition_forbidden_terms(v: Vocabulary, opts: dict[str, Any]) -> list[tuple[str, str]]:
    pats = [re.compile(p) for p in opts.get("patterns") or []]
    out = []
    for s, c in v.concepts.items():
        for p in pats:
            for m in p.finditer(c["definition"]):
                out.append((s, f"definition mentions “{m.group(0)}”", {"term": m.group(0)}))
    return out


SEVERITY_ORDER = {"error": 0, "warn": 1, "info": 2}


def run_checks(v: Vocabulary) -> list[dict[str, Any]]:
    """Attach `flags` to every concept; return the list of enabled checks with counts."""
    cfg = (v.cfg.section("quality").get("checks")) or {}
    for c in v.concepts.values():
        c["flags"] = []
    summary = []
    for name, opts in cfg.items():
        opts = opts or {}
        if opts.get("enabled") is False:
            continue
        if name not in CHECKS:
            raise SystemExit(f"unknown quality check in config: {name}")
        severity = opts.get("severity", "warn")
        hits = CHECKS[name](v, opts)
        skip = set(opts.get("skip_under") or [])
        if skip:
            hits = [h for h in hits if h[0] in v.concepts and not _branch_value(v, h[0], {k: True for k in skip}, False)]
        for slug, detail, *extra in hits:
            if slug in v.concepts:
                v.concepts[slug]["flags"].append(
                    {
                        "check": name,
                        "severity": severity,
                        "detail": detail,
                        "refs": [r for r in dict.fromkeys(REF_RE.findall(detail)) if r in v.concepts],
                        **(extra[0] if extra else {}),
                    }
                )
        summary.append({"check": name, "severity": severity, "count": len({h[0] for h in hits})})
    for c in v.concepts.values():
        c["flags"].sort(key=lambda f: (SEVERITY_ORDER.get(f["severity"], 9), f["check"]))
    summary.sort(key=lambda s: (SEVERITY_ORDER.get(s["severity"], 9), s["check"]))
    return summary
