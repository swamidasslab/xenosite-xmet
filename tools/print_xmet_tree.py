#!/usr/bin/env python3
"""Pretty-print an XMET concept tree for review.

Default: whole ontology from ``xenobiotic biotransformation``. Annotates Forest
and tagger SSSOM subjects when present (direct mappings only). After the tree,
lists intra-tree relations (relatedTo / antonymOf / hasPart / isPartOf) and
prints depth / breadth statistics.

Examples:
  uv run python tools/print_xmet_tree.py
  uv run python tools/print_xmet_tree.py --root \"reaction class\"
  uv run python tools/print_xmet_tree.py --root xmet:4000009 --depth 3
  make ontology-tree
"""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
YAML_PATH = ROOT / "data/ontology/xmet.yaml"
FOREST_SSSOM = ROOT / "data/mappings/xmet-forest.sssom.tsv"
TAGGER_SSSOM = ROOT / "data/mappings/xmet-tagger.sssom.tsv"

ONTOLOGY_ROOT = "xmet:4000000"  # xenobiotic biotransformation
REACTION_DESCRIPTOR = "xmet:4000263"


def load_concepts() -> dict[str, dict[str, Any]]:
    data = yaml.safe_load(YAML_PATH.read_text())
    return {c["id"]: c for c in data["concepts"]}


def children_map(by: dict[str, dict[str, Any]]) -> dict[str, list[str]]:
    ch: dict[str, list[str]] = defaultdict(list)
    for cid, c in by.items():
        for p in c.get("parents") or []:
            ch[p].append(cid)
    for p in ch:
        ch[p].sort(key=lambda i: ((by[i].get("preferred_label") or "").lower(), i))
    return ch


def load_sssom_index(path: Path) -> dict[str, list[tuple[str, str]]]:
    """subject_id → [(predicate, object_id), ...]"""
    if not path.exists():
        return {}
    out: dict[str, list[tuple[str, str]]] = defaultdict(list)
    with path.open() as fh:
        reader = csv.DictReader((ln for ln in fh if not ln.startswith("#")), delimiter="\t")
        for row in reader:
            sub = row.get("subject_id") or ""
            pred = (row.get("predicate_id") or "").replace("skos:", "")
            obj = row.get("object_id") or ""
            if sub and obj:
                out[sub].append((pred, obj))
    return out


def load_always_with_incoming(path: Path) -> dict[str, list[tuple[str, str]]]:
    """descriptor_id → [(site_subject_id, forest_object_id), ...] from SSSOM always_with."""
    if not path.exists():
        return {}
    out: dict[str, list[tuple[str, str]]] = defaultdict(list)
    with path.open() as fh:
        reader = csv.DictReader((ln for ln in fh if not ln.startswith("#")), delimiter="\t")
        for row in reader:
            sub = row.get("subject_id") or ""
            obj = row.get("object_id") or ""
            raw = (row.get("always_with") or "").strip()
            if not sub or not raw:
                continue
            for desc in raw.split("|"):
                desc = desc.strip()
                if desc:
                    out[desc].append((sub, obj))
    for desc in out:
        out[desc].sort(key=lambda t: (t[0], t[1]))
    return out


def under_reaction_descriptor(
    cid: str, by: dict[str, dict[str, Any]], memo: dict[str, bool] | None = None
) -> bool:
    """True if cid is reaction descriptor or a broader-descendant of it."""
    if memo is None:
        memo = {}
    if cid in memo:
        return memo[cid]
    if cid == REACTION_DESCRIPTOR:
        memo[cid] = True
        return True
    c = by.get(cid) or {}
    ok = any(
        under_reaction_descriptor(p, by, memo) for p in (c.get("parents") or [])
    )
    memo[cid] = ok
    return ok


def resolve_root(by: dict[str, dict[str, Any]], root: str) -> str:
    if root in by:
        return root
    want = root.strip().lower()
    hits = [
        cid
        for cid, c in by.items()
        if (c.get("preferred_label") or "").lower() == want
        or want in [(s or "").lower() for s in (c.get("synonyms") or [])]
    ]
    if len(hits) == 1:
        return hits[0]
    if not hits:
        raise SystemExit(f"root not found: {root!r}")
    raise SystemExit(
        f"ambiguous root label {root!r}; matches: "
        + ", ".join(f"{h} ({by[h].get('preferred_label')})" for h in hits[:8])
    )


def _rank_obj(obj: str) -> int:
    if obj.startswith("forest.pattern:"):
        return 0
    if obj.startswith("forest.rule:"):
        return 1
    if obj.startswith("rule:"):
        return 2
    if obj.startswith("forest.ruleset:"):
        return 3
    return 4


def _short_obj(obj: str) -> str:
    if obj.startswith("forest.pattern:"):
        return "pattern:" + obj.split(":", 1)[1]
    if obj.startswith("forest.rule:"):
        return "rule:" + obj.split(":", 1)[1]
    if obj.startswith("forest.ruleset:"):
        return "ruleset:" + obj.split(":", 1)[1]
    if obj.startswith("rule:"):
        return "tagger:" + obj.removeprefix("rule:")
    return obj


def format_mapping_rows(
    rows: list[tuple[str, str]],
    *,
    prefix: str = "",
    limit: int = 4,
) -> str:
    if not rows:
        return ""
    rows = sorted(rows, key=lambda t: (_rank_obj(t[1]), t[1]))
    bits = []
    for pred, obj in rows[:limit]:
        mark = "exact" if pred == "exactMatch" else pred
        bits.append(f"{mark}→{_short_obj(obj)}")
    extra = f" +{len(rows) - limit}" if len(rows) > limit else ""
    body = "; ".join(bits) + extra
    if prefix:
        return f"  [{prefix}{body}]"
    return f"  [{body}]"


def mapping_note(
    cid: str,
    forest: dict[str, list[tuple[str, str]]],
    tagger: dict[str, list[tuple[str, str]]],
    by: dict[str, dict[str, Any]],
    *,
    show_forest: bool,
    show_tagger: bool,
    always_with_in: dict[str, list[tuple[str, str]]] | None = None,
    show_incoming_always_with: bool = True,
) -> str:
    bits: list[str] = []
    own_forest = list(forest.get(cid) or []) if show_forest else []
    own_tagger = list(tagger.get(cid) or []) if show_tagger else []

    if own_forest:
        bits.append(format_mapping_rows(own_forest).strip())

    if own_tagger:
        bits.append(format_mapping_rows(own_tagger).strip())

    parts = by.get(cid, {}).get("has_part") or []
    if parts:
        labs = []
        for p in parts[:4]:
            labs.append((by.get(p) or {}).get("preferred_label") or p)
        extra = f" +{len(parts)-4}" if len(parts) > 4 else ""
        bits.append("[hasPart: " + "; ".join(labs) + extra + "]")

    related = by.get(cid, {}).get("related_to") or []
    if related:
        labs = []
        for p in related[:4]:
            labs.append((by.get(p) or {}).get("preferred_label") or p)
        extra = f" +{len(related)-4}" if len(related) > 4 else ""
        bits.append("[relatedTo: " + "; ".join(labs) + extra + "]")

    always = by.get(cid, {}).get("always_with") or []
    if always:
        labs = []
        for p in always[:4]:
            labs.append((by.get(p) or {}).get("preferred_label") or p)
        extra = f" +{len(always)-4}" if len(always) > 4 else ""
        bits.append("[alwaysWith: " + "; ".join(labs) + extra + "]")

    suggests = by.get(cid, {}).get("suggests") or []
    if suggests:
        labs = []
        for p in suggests[:4]:
            labs.append((by.get(p) or {}).get("preferred_label") or p)
        extra = f" +{len(suggests)-4}" if len(suggests) > 4 else ""
        bits.append("[suggests: " + "; ".join(labs) + extra + "]")

    # Incoming Forest SSSOM alwaysWith on reaction-descriptor spine
    if (
        show_incoming_always_with
        and always_with_in
        and under_reaction_descriptor(cid, by)
    ):
        incoming = always_with_in.get(cid) or []
        if incoming:
            labs = []
            for site_id, forest_obj in incoming[:6]:
                site = (by.get(site_id) or {}).get("preferred_label") or site_id
                labs.append(f"{site}←{_short_obj(forest_obj)}")
            extra = f" +{len(incoming)-6}" if len(incoming) > 6 else ""
            bits.append("[←alwaysWith: " + "; ".join(labs) + extra + "]")

    if not bits:
        return ""
    return " " + " ".join(bits)


def walk(
    cid: str,
    by: dict[str, dict[str, Any]],
    children: dict[str, list[str]],
    forest: dict[str, list[tuple[str, str]]],
    tagger: dict[str, list[tuple[str, str]]],
    *,
    depth: int,
    max_depth: int | None,
    show_ids: bool,
    show_forest: bool,
    show_tagger: bool,
    always_with_in: dict[str, list[tuple[str, str]]] | None = None,
    prefix: str = "",
    is_last: bool = True,
    seen: set[str] | None = None,
) -> list[str]:
    if seen is None:
        seen = set()
    lines: list[str] = []
    c = by[cid]
    label = c.get("preferred_label") or cid
    id_bit = f"  ({cid})" if show_ids else ""
    map_bit = mapping_note(
        cid,
        forest,
        tagger,
        by,
        show_forest=show_forest,
        show_tagger=show_tagger,
        always_with_in=always_with_in,
    )
    branch = "└── " if is_last else "├── "
    if depth == 0:
        lines.append(f"{label}{id_bit}{map_bit}")
    else:
        lines.append(f"{prefix}{branch}{label}{id_bit}{map_bit}")

    if cid in seen:
        return lines
    seen = seen | {cid}

    if max_depth is not None and depth >= max_depth:
        kids = children.get(cid) or []
        if kids:
            cont = prefix + ("    " if is_last else "│   ")
            lines.append(f"{cont}… ({len(kids)} children)")
        return lines

    kids = children.get(cid) or []
    for i, kid in enumerate(kids):
        last = i == len(kids) - 1
        cont = "" if depth == 0 else prefix + ("    " if is_last else "│   ")
        lines.extend(
            walk(
                kid,
                by,
                children,
                forest,
                tagger,
                depth=depth + 1,
                max_depth=max_depth,
                show_ids=show_ids,
                show_forest=show_forest,
                show_tagger=show_tagger,
                always_with_in=always_with_in,
                prefix=cont if depth > 0 else "",
                is_last=last,
                seen=seen,
            )
        )
    return lines


def collect_subtree(
    root: str,
    children: dict[str, list[str]],
    *,
    max_depth: int | None = None,
) -> tuple[set[str], dict[str, int]]:
    """Return nodes in the printed subtree and depth (from root) per node."""
    depths: dict[str, int] = {root: 0}
    stack = [root]
    while stack:
        cid = stack.pop()
        d = depths[cid]
        if max_depth is not None and d >= max_depth:
            continue
        for kid in children.get(cid) or []:
            if kid in depths:
                continue
            depths[kid] = d + 1
            stack.append(kid)
    return set(depths), depths


def _label(by: dict[str, dict[str, Any]], cid: str) -> str:
    return (by.get(cid) or {}).get("preferred_label") or cid


def _median(vals: list[float | int]) -> float:
    if not vals:
        return 0.0
    s = sorted(vals)
    n = len(s)
    mid = n // 2
    if n % 2:
        return float(s[mid])
    return (s[mid - 1] + s[mid]) / 2.0


def _mean(vals: list[float | int]) -> float:
    return sum(vals) / len(vals) if vals else 0.0


# Intra-ontology link fields (not skos:broader — that is the tree itself).
INTRA_REL_FIELDS: list[tuple[str, str]] = [
    ("related_to", "relatedTo"),
    ("suggests", "suggests"),
    ("always_with", "alwaysWith"),
    ("operationalizes", "operationalizes"),
    ("predicts", "predicts"),
    ("recognizes", "recognizes"),
    ("enumerates", "enumerates"),
    ("antonyms", "antonymOf"),
    ("has_part", "hasPart"),
    ("is_part_of", "isPartOf"),
]


def format_intra_relations(
    by: dict[str, dict[str, Any]],
    subtree: set[str],
) -> list[str]:
    """List non-hierarchy links with both ends inside the subtree."""
    edges: list[tuple[str, str, str, str]] = []  # (rel, src, dst, undirected_key)
    seen_undirected: set[tuple[str, str, str]] = set()
    for cid in sorted(subtree, key=lambda i: (_label(by, i).lower(), i)):
        c = by.get(cid) or {}
        for field, rel in INTRA_REL_FIELDS:
            for tgt in c.get(field) or []:
                if tgt not in subtree:
                    continue
                if rel == "antonymOf":
                    key = (rel, *sorted((cid, tgt)))
                    if key in seen_undirected:
                        continue
                    seen_undirected.add(key)
                edges.append((rel, cid, tgt, ""))

    lines = ["", f"Intra-tree relations ({len(edges)}):"]
    if not edges:
        lines.append("  (none)")
        return lines

    by_rel: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for rel, src, dst, _ in edges:
        by_rel[rel].append((src, dst))

    for rel in ("relatedTo", "suggests", "alwaysWith", "antonymOf", "hasPart", "isPartOf"):
        pairs = by_rel.get(rel) or []
        if not pairs:
            continue
        lines.append(f"  {rel} ({len(pairs)}):")
        for src, dst in sorted(
            pairs, key=lambda t: (_label(by, t[0]).lower(), _label(by, t[1]).lower())
        ):
            lines.append(f"    {_label(by, src)}  —{rel}→  {_label(by, dst)}")
    return lines


def format_tree_stats(
    by: dict[str, dict[str, Any]],
    children: dict[str, list[str]],
    root: str,
    subtree: set[str],
    depths: dict[str, int],
) -> list[str]:
    """Depth and per-level breadth statistics for the printed subtree."""
    depth_vals = list(depths.values())
    max_d = max(depth_vals) if depth_vals else 0

    # Breadth at depth d = number of nodes at that depth.
    nodes_at: dict[int, int] = defaultdict(int)
    for d in depth_vals:
        nodes_at[d] += 1
    breadth_at = [nodes_at[d] for d in range(0, max_d + 1)]

    # Children counts for every node at each depth (leaves contribute 0).
    children_at: dict[int, list[int]] = defaultdict(list)
    for cid, d in depths.items():
        n_kids = sum(1 for k in (children.get(cid) or []) if k in subtree)
        children_at[d].append(n_kids)

    branching = [n for vals in children_at.values() for n in vals if n > 0]

    lines = [
        "",
        "Tree statistics:",
        f"  nodes: {len(subtree)}",
        f"  depth (root=0):  avg={_mean(depth_vals):.2f}  median={_median(depth_vals):.1f}  max={max_d}",
        f"  breadth by depth (# nodes at depth):",
    ]
    for d, b in enumerate(breadth_at):
        lines.append(f"    depth {d}: {b}")
    if breadth_at:
        lines.append(
            f"  breadth summary (over depths 0..{max_d}):  "
            f"avg={_mean(breadth_at):.2f}  median={_median(breadth_at):.1f}  max={max(breadth_at)}"
        )
    lines.append("  avg children by depth (internal nodes only; leaves excluded):")
    for d in range(0, max_d + 1):
        vals = [n for n in (children_at.get(d) or []) if n > 0]
        if not vals:
            lines.append(f"    depth {d}: (no internal nodes)")
        else:
            lines.append(
                f"    depth {d}: n_internal={len(vals)}  "
                f"avg_children={_mean(vals):.2f}  median={_median(vals):.1f}  max={max(vals)}"
            )
    if branching:
        lines.append(
            f"  branching factor (internal nodes only):  "
            f"avg={_mean(branching):.2f}  median={_median(branching):.1f}  max={max(branching)}"
        )
    leaves = sum(1 for vals in children_at.values() for n in vals if n == 0)
    lines.append(f"  leaves: {leaves}")
    return lines


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--root",
        default=ONTOLOGY_ROOT,
        help="Root concept id or preferred_label "
        "(default: whole ontology / xenobiotic biotransformation)",
    )
    ap.add_argument(
        "--depth",
        type=int,
        default=None,
        help="Max depth from root (default: unlimited)",
    )
    ap.add_argument("--ids", action="store_true", help="Show xmet: ids")
    ap.add_argument(
        "--no-forest",
        action="store_true",
        help="Omit Forest SSSOM annotations",
    )
    ap.add_argument(
        "--no-tagger",
        action="store_true",
        help="Omit tagger SMARTS SSSOM annotations",
    )
    ap.add_argument(
        "--stats",
        action="store_true",
        help="Also print Forest/tagger SSSOM coverage counts",
    )
    ap.add_argument(
        "--no-relations",
        action="store_true",
        help="Omit intra-tree relatedTo/antonymOf/hasPart listing",
    )
    ap.add_argument(
        "--no-shape-stats",
        action="store_true",
        help="Omit depth/breadth statistics",
    )
    args = ap.parse_args()

    by = load_concepts()
    children = children_map(by)
    forest = {} if args.no_forest else load_sssom_index(FOREST_SSSOM)
    tagger = {} if args.no_tagger else load_sssom_index(TAGGER_SSSOM)
    always_with_in = {} if args.no_forest else load_always_with_incoming(FOREST_SSSOM)
    root = resolve_root(by, args.root)

    lines = walk(
        root,
        by,
        children,
        forest,
        tagger,
        depth=0,
        max_depth=args.depth,
        show_ids=args.ids,
        show_forest=not args.no_forest,
        show_tagger=not args.no_tagger,
        always_with_in=always_with_in,
    )
    print("\n".join(lines))

    subtree, depths = collect_subtree(root, children, max_depth=args.depth)

    if not args.no_relations:
        print("\n".join(format_intra_relations(by, subtree)))

    if not args.no_shape_stats:
        print("\n".join(format_tree_stats(by, children, root, subtree, depths)))

    if args.stats:
        with_forest = sum(1 for cid in subtree if forest.get(cid))
        with_tagger = sum(1 for cid in subtree if tagger.get(cid))
        exact_pat = 0
        for cid in subtree:
            for pred, obj in forest.get(cid) or []:
                if pred == "exactMatch" and obj.startswith("forest.pattern:"):
                    exact_pat += 1
                    break
        print()
        print("Mapping coverage:")
        print(f"  with Forest SSSOM: {with_forest}")
        print(f"  with exactMatch forest.pattern: {exact_pat}")
        print(f"  with tagger SSSOM: {with_tagger}")


if __name__ == "__main__":
    main()
