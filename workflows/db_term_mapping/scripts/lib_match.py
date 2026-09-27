"""Shared helpers for DB term → XRM matching."""
from __future__ import annotations

import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import yaml

# Unicode dashes → ASCII hyphen
_DASHES = re.compile(r"[\u2010-\u2015\u2212−]")
_NON_ALNUM = re.compile(r"[^a-z0-9+\s\-/]")
_WS = re.compile(r"\s+")
# "O - glucuronidation" / "Oglucuronidation" edge cases handled lightly
_HETERO_PREFIX = re.compile(r"\b([ons])[\s\-]+(?=[a-z])", re.I)
_GSH = re.compile(r"\bgsh\b", re.I)


_REGIO = (
    (re.compile(r"\bp-(?=hydrox|oh\b|substit)", re.I), "para-"),
    (re.compile(r"\bo-(?=hydrox|oh\b|substit)", re.I), "ortho-"),
    (re.compile(r"\bm-(?=hydrox|oh\b|substit)", re.I), "meta-"),
)


def normalize_label(text: str) -> str:
    """Casefold and light canonicalize for exact matching."""
    s = (text or "").strip().lower()
    s = _DASHES.sub("-", s)
    s = s.replace("_", " ")
    s = _GSH.sub("gsh", s)
    for pat, repl in _REGIO:
        s = pat.sub(repl, s)
    s = _HETERO_PREFIX.sub(lambda m: m.group(1).lower() + "-", s)
    s = _NON_ALNUM.sub(" ", s)
    s = s.replace(" - ", "-")
    s = _WS.sub(" ", s).strip()
    # unify common spelling variants that are not true synonyms in ontology
    s = s.replace("sulphonation", "sulfonation")
    s = s.replace("sulphation", "sulfation")
    s = s.replace("hydroxlation", "hydroxylation")
    s = s.replace("deydroxylation", "dehydroxylation")
    s = s.replace("oxdation", "oxidation")
    s = s.replace("thiohene", "thiophene")
    return s


# Heads that often appear in site-qualified MetX phrases ("X of Y", "X on Y")
COMPOSITIONAL_HEADS = [
    "aromatic hydroxylation",
    "aliphatic hydroxylation",
    "para-hydroxylation",
    "ortho-hydroxylation",
    "meta-hydroxylation",
    "benzylic hydroxylation",
    "allylic hydroxylation",
    "alicyclic hydroxylation",
    "hydroxylation",
    "n-dealkylation",
    "o-dealkylation",
    "s-dealkylation",
    "aromatic o-dealkylation",
    "n-demethylation",
    "o-demethylation",
    "o-glucuronidation",
    "glucuronidation",
    "o-sulfation",
    "sulfation",
    "sulfonation",
    "epoxidation",
    "n-oxidation",
    "s-oxidation",
    "n-hydroxylation",
    "oxidation",
    "reduction",
    "hydrolysis",
    "glutathionation",
    "gsh conjugation",
    "glutathione conjugation",
    "acetylation",
    "methylation",
    "dealkylation",
    "dearylation",
    "desulfuration",
]

_COMPOSITIONAL_SPLIT = re.compile(
    r"\s+(?:of|on|at|to|via|with|from|adjacent to|not)\s+",
    re.I,
)


def compositional_head(term: str) -> str | None:
    """If term looks like '<reaction> of|on <site…>', return normalized head."""
    n = normalize_label(term)
    # Aromatic -OH glucuronidation style
    if " -oh " in f" {n} " or n.endswith(" -oh glucuronidation") or "-oh glucuronidation" in n:
        if "glucuron" in n:
            return "o-glucuronidation"
    if " of " not in n and " on " not in n and " adjacent " not in n:
        # still allow "Hydroxylation of …" already covered; "p-Hydroxylation of …"
        if not _COMPOSITIONAL_SPLIT.search(n):
            return None
    # Prefer longest matching known head as prefix
    heads = sorted(COMPOSITIONAL_HEADS, key=len, reverse=True)
    for h in heads:
        if n == h:
            return None  # bare head, not compositional
        if n.startswith(h + " ") or n.startswith(h + "-"):
            rest = n[len(h) :].lstrip(" -")
            if rest and not rest.startswith("("):
                return h
    # generic: first clause before of/on
    parts = _COMPOSITIONAL_SPLIT.split(n, maxsplit=1)
    if len(parts) == 2 and parts[0].strip() and parts[1].strip():
        return parts[0].strip()
    return None


def load_ontology(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text())


def spine_map(raw: dict[str, Any]) -> dict[str, str]:
    return {s["id"]: s["preferred_label"] for s in raw["spines"]}


def concept_index(
    raw: dict[str, Any],
    match_spines: set[str],
) -> tuple[dict[str, list[dict[str, str]]], dict[str, dict[str, str]]]:
    """Return (norm_label → candidate list, concept_id → meta)."""
    spines = spine_map(raw)
    concepts = raw["concepts"]
    by_id: dict[str, dict[str, Any]] = {c["id"]: c for c in concepts}
    for s in raw["spines"]:
        by_id[s["id"]] = {**s, "parents": []}

    def parents_of(c: dict[str, Any]) -> list[str]:
        p = c.get("parents") or []
        return [p] if isinstance(p, str) else list(p)

    def nearest_spine(cid: str, seen: set[str] | None = None) -> str | None:
        seen = seen or set()
        if cid in spines:
            return cid
        if cid in seen or cid not in by_id:
            return None
        seen.add(cid)
        for b in parents_of(by_id[cid]):
            r = nearest_spine(b, seen)
            if r:
                return r
        return None

    meta: dict[str, dict[str, str]] = {}
    idx: dict[str, list[dict[str, str]]] = defaultdict(list)

    for c in concepts:
        sid = nearest_spine(c["id"])
        sname = spines.get(sid or "", "none")
        if sname not in match_spines:
            continue
        pref = c["preferred_label"]
        meta[c["id"]] = {
            "preferred_label": pref,
            "spine": sname,
            "definition": (c.get("definition") or "")[:240],
        }
        labels = [(pref, "pref")] + [(s, "synonym") for s in (c.get("synonyms") or []) if s]
        for lab, kind in labels:
            n = normalize_label(lab)
            if not n:
                continue
            idx[n].append(
                {
                    "xrm_id": c["id"],
                    "preferred_label": pref,
                    "spine": sname,
                    "matched_label": lab,
                    "label_kind": kind,
                }
            )
    return idx, meta


def load_aliases(path: Path) -> dict[str, dict[str, str]]:
    """aliases.tsv: source_term, xrm_id, preferred_label, note"""
    if not path.exists():
        return {}
    out: dict[str, dict[str, str]] = {}
    import csv

    with path.open() as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            term = (row.get("source_term") or "").strip()
            if not term or term.startswith("#"):
                continue
            out[normalize_label(term)] = {
                "xrm_id": row["xrm_id"].strip(),
                "preferred_label": row.get("preferred_label", "").strip(),
                "note": row.get("note", "").strip(),
            }
    return out


def load_adjudications(path: Path) -> dict[tuple[str, str], dict[str, str]]:
    """Keyed by (source, term_norm)."""
    if not path.exists():
        return {}
    import csv

    out: dict[tuple[str, str], dict[str, str]] = {}
    with path.open() as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            src = row["source"].strip()
            term = row["term"].strip()
            out[(src, normalize_label(term))] = row
    return out


def write_tsv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    import csv

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as fh:
        w = csv.DictWriter(
            fh,
            fieldnames=fieldnames,
            delimiter="\t",
            lineterminator="\n",
            extrasaction="ignore",
        )
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fieldnames})


def read_term_counts(path: Path, source: str) -> list[dict[str, Any]]:
    import csv

    rows = []
    with path.open() as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            term = (row.get("term") or "").strip()
            if not term or term in {"(empty)", "(null)"}:
                continue
            rows.append(
                {
                    "source": source,
                    "term": term,
                    "count": int(row["count"]),
                    "field": row.get("field", ""),
                }
            )
    return rows
