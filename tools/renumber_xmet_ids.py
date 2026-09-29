#!/usr/bin/env python3
"""Renumber live XMET concept IDs to a dense opaque block.

Default start: ``xmet:4000000`` (empty block — does not overlap legacy
``0/1/2/3xxxxxx`` live IDs). IDs do **not** encode hierarchy.

Also rewrites historical/retired CURIEs found in ``xmet-id-remap.tsv`` to their
final live targets (merge chain → new id).

Coverage:
  - ``data/ontology/xmet.yaml`` (+ regenerate SKOS afterward)
  - all ``data/mappings/**`` SSSOM / views / expectations / remap
  - tools, tests, competency, workflows, docs in this repo
  - sibling ``crates/xenosite-tagger`` and ``crates/xenosite-tagger-forest``

Writes ``data/mappings/xmet-id-renumber.tsv`` and appends ``renumbered`` rows to
``data/mappings/xmet-id-remap.tsv``.

Usage::

    uv run python tools/renumber_xmet_ids.py --dry-run
    uv run python tools/renumber_xmet_ids.py
    make ontology-export && make validate-redesign
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
YAML_PATH = ROOT / "data/ontology/xmet.yaml"
RENUMBER_TSV = ROOT / "data/mappings/xmet-id-renumber.tsv"
REMAP_TSV = ROOT / "data/mappings/xmet-id-remap.tsv"
DEFAULT_START = 4_000_000
ONTOLOGY_ROOT_OLD = "xmet:0000000"

CURIE_RE = re.compile(r"xmet:(\d{7})\b")
PLACEHOLDER_RE = re.compile(r"xmet:__RENUM_(\d{7})__")

INCLUDE_GLOBS = [
    "data/ontology/xmet.yaml",
    "data/ontology/ANNOTATION.md",
    "data/ontology/RELATED_ONTOLOGIES.md",
    "data/ontology/site_templates.yml",
    "data/mappings/**/*",
    "data/assignments/**/*",
    "data/candidates/**/*",
    "data/competency/**/*",
    "data/derived/**/*",
    "data/samples/**/*",
    "docs/**/*",
    "revision/**/*",
    "tests/**/*",
    "tools/**/*",
    "workflows/**/*",
    "LOG.md",
    "TODO.md",
    "README.md",
    "Makefile",
]

SKIP_DIR_NAMES = {".git", "target", ".venv", "artifacts", "node_modules"}
SKIP_NAMES = {
    "renumber_xmet_ids.py",
    "xmet.skos.jsonld",
    "xmet.skos.ttl",
    "xmet.ttl",
    "xmet-id-renumber.tsv",  # written separately; must keep old_id column
    "xmet-id-remap.tsv",  # rewritten specially (preserve historical old_id)
}
SKIP_SUFFIXES = {".pyc", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".o", ".a"}


def load_concepts() -> list[dict]:
    return list(yaml.safe_load(YAML_PATH.read_text())["concepts"])


def build_live_map(concepts: list[dict], start: int) -> dict[str, str]:
    ids = [c["id"] for c in concepts]
    if len(ids) != len(set(ids)):
        raise SystemExit("duplicate concept ids in YAML")
    # Refuse overlap with any live id.
    live_nums = {int(i.split(":")[1]) for i in ids}
    span = set(range(start, start + len(ids)))
    overlap = live_nums & span
    if overlap:
        raise SystemExit(
            f"start={start} overlaps {len(overlap)} live ids "
            f"(e.g. xmet:{min(overlap):07d}). choose an empty block."
        )
    ordered: list[str] = []
    if ONTOLOGY_ROOT_OLD in ids:
        ordered.append(ONTOLOGY_ROOT_OLD)
    ordered.extend(sorted(i for i in ids if i != ONTOLOGY_ROOT_OLD))
    return {old: f"xmet:{start + i:07d}" for i, old in enumerate(ordered)}


def load_remap_edges() -> dict[str, str]:
    if not REMAP_TSV.exists():
        return {}
    edge: dict[str, str] = {}
    with REMAP_TSV.open() as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            old = (row.get("old_id") or "").strip()
            new = (row.get("new_id") or "").strip()
            ctype = (row.get("change_type") or "").strip()
            if ctype == "renumbered":
                continue
            if old and new and old != new:
                edge[old] = new
    return edge


def build_alias_map(live: dict[str, str], edges: dict[str, str]) -> dict[str, str]:
    """Map every known CURIE (live or historical) → final new id."""
    aliases = dict(live)

    def resolve(cid: str, seen: set[str] | None = None) -> str | None:
        if cid in live:
            return live[cid]
        if cid in aliases and aliases[cid] != cid:
            # already final-ish
            if aliases[cid] in live.values():
                return aliases[cid]
        if seen is None:
            seen = set()
        if cid in seen:
            return None
        seen.add(cid)
        nxt = edges.get(cid)
        if not nxt:
            return None
        if nxt in live:
            return live[nxt]
        return resolve(nxt, seen)

    for old in list(edges):
        final = resolve(old)
        if final:
            aliases[old] = final
    return aliases


def to_placeholders(text: str, aliases: dict[str, str]) -> tuple[str, int]:
    n = 0

    def repl(m: re.Match[str]) -> str:
        nonlocal n
        old = f"xmet:{m.group(1)}"
        new = aliases.get(old)
        if not new or new == old:
            return m.group(0)
        n += 1
        num = new.split(":")[1]
        return f"xmet:__RENUM_{num}__"

    return CURIE_RE.sub(repl, text), n


def from_placeholders(text: str) -> str:
    return PLACEHOLDER_RE.sub(r"xmet:\1", text)


def iter_target_files(extra_roots: list[Path]) -> list[Path]:
    files: set[Path] = set()
    for pattern in INCLUDE_GLOBS:
        for p in ROOT.glob(pattern):
            if p.is_file():
                files.add(p.resolve())
    for er in extra_roots:
        if not er.is_dir():
            continue
        for p in er.rglob("*"):
            if not p.is_file():
                continue
            if any(part in SKIP_DIR_NAMES for part in p.parts):
                continue
            if p.suffix.lower() in SKIP_SUFFIXES or p.name in SKIP_NAMES:
                continue
            try:
                if "xmet:" not in p.read_text(encoding="utf-8", errors="ignore")[:200_000]:
                    continue
            except OSError:
                continue
            files.add(p.resolve())
    out: list[Path] = []
    for p in sorted(files):
        if p.name in SKIP_NAMES:
            continue
        if any(part in SKIP_DIR_NAMES for part in p.parts):
            continue
        if p.resolve() == Path(__file__).resolve():
            continue
        out.append(p)
    return out


def write_renumber_tsv(live: dict[str, str], concepts_by_id: dict[str, dict]) -> None:
    RENUMBER_TSV.parent.mkdir(parents=True, exist_ok=True)
    with RENUMBER_TSV.open("w", newline="") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n")
        w.writerow(["old_id", "new_id", "preferred_label"])
        for old, new in sorted(live.items(), key=lambda kv: kv[1]):
            lab = (concepts_by_id.get(old) or {}).get("preferred_label") or ""
            w.writerow([old, new, lab])


def rewrite_remap_tsv(aliases: dict[str, str], live: dict[str, str], start: int) -> None:
    """Preserve historical old_id; rewrite new_id to final; append renumber rows."""
    if REMAP_TSV.exists():
        rows = list(csv.DictReader(REMAP_TSV.open(), delimiter="\t"))
        fieldnames = ["old_id", "new_id", "change_type", "note"]
    else:
        rows = []
        fieldnames = ["old_id", "new_id", "change_type", "note"]

    out_rows: list[dict[str, str]] = []
    for row in rows:
        if (row.get("change_type") or "").strip() == "renumbered":
            continue
        new = (row.get("new_id") or "").strip()
        if new and new in aliases:
            row = dict(row)
            row["new_id"] = aliases[new]
        out_rows.append(row)

    for old, new in sorted(live.items(), key=lambda kv: kv[1]):
        if old == new:
            continue
        out_rows.append(
            {
                "old_id": old,
                "new_id": new,
                "change_type": "renumbered",
                "note": f"dense opaque renumber to xmet:{start}+",
            }
        )

    with REMAP_TSV.open("w", newline="") as fh:
        w = csv.DictWriter(
            fh, fieldnames=fieldnames, delimiter="\t", lineterminator="\n", extrasaction="ignore"
        )
        w.writeheader()
        for row in out_rows:
            w.writerow({k: row.get(k) or "" for k in fieldnames})


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--start", type=int, default=DEFAULT_START)
    ap.add_argument("--no-tagger", action="store_true")
    args = ap.parse_args()
    start = args.start

    concepts = load_concepts()
    ids = {c["id"] for c in concepts}
    if ONTOLOGY_ROOT_OLD not in ids and f"xmet:{start:07d}" in ids:
        print("looks already renumbered; abort.", file=sys.stderr)
        return 1

    live = build_live_map(concepts, start)
    edges = load_remap_edges()
    aliases = build_alias_map(live, edges)
    concepts_by_id = {c["id"]: c for c in concepts}

    print(f"live concepts={len(live)}  aliases={len(aliases)}")
    print(f"root {ONTOLOGY_ROOT_OLD} → {live[ONTOLOGY_ROOT_OLD]}")
    print(f"last → {sorted(live.items(), key=lambda kv: kv[1])[-1]}")

    extra: list[Path] = []
    if not args.no_tagger:
        for name in ("xenosite-tagger", "xenosite-tagger-forest"):
            p = ROOT.parent / "crates" / name
            if p.is_dir():
                extra.append(p)
                print(f"also scanning {p}")

    targets = iter_target_files(extra)
    print(f"candidate files: {len(targets)}")

    total_hits = 0
    touched = 0
    for path in targets:
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if not CURIE_RE.search(text):
            continue
        phased, n = to_placeholders(text, aliases)
        if n == 0:
            continue
        new_text = from_placeholders(phased)
        total_hits += n
        touched += 1
        try:
            rel: Path | str = path.relative_to(ROOT)
        except ValueError:
            rel = path
        print(f"  {rel}: {n}")
        if not args.dry_run:
            path.write_text(new_text)

    if args.dry_run:
        print(f"dry-run: would touch {touched} files ({total_hits} CURIE hits)")
        return 0

    write_renumber_tsv(live, concepts_by_id)
    rewrite_remap_tsv(aliases, live, start)
    print(f"wrote {RENUMBER_TSV.relative_to(ROOT)}")
    print(f"updated {REMAP_TSV.relative_to(ROOT)}")
    print(f"done: {touched} files, {total_hits} CURIE replacements")
    print("next: make ontology-export && make validate-redesign")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
