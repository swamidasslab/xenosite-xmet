#!/usr/bin/env python3
"""Fuzzy-scan XMET labels for candidate duplicates and misparenting.

Uses rapidfuzz when available, else difflib. Prints ranked candidates; exit 0
always (audit, not a hard gate). Wire into CI later if desired.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
YAML_PATH = ROOT / "data/ontology/xmet.yaml"

try:
    from rapidfuzz import fuzz

    ENGINE = "rapidfuzz"
except ImportError:  # pragma: no cover
    from difflib import SequenceMatcher

    ENGINE = "difflib"

    class fuzz:  # type: ignore[no-redef]
        @staticmethod
        def ratio(a: str, b: str) -> float:
            return 100 * SequenceMatcher(None, a, b).ratio()

        @staticmethod
        def token_sort_ratio(a: str, b: str) -> float:
            ta = " ".join(sorted(a.split()))
            tb = " ".join(sorted(b.split()))
            return 100 * SequenceMatcher(None, ta, tb).ratio()

        @staticmethod
        def partial_ratio(a: str, b: str) -> float:
            if a in b or b in a:
                return 100 * min(len(a), len(b)) / max(len(a), len(b))
            return fuzz.ratio(a, b)


def norm(s: str) -> str:
    s = s.lower().replace("–", "-").replace("—", "-")
    s = re.sub(r"[^a-z0-9+/\s-]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def ancestors(cid: str, pm: dict[str, list[str]], memo: dict[str, set[str]]) -> set[str]:
    if cid in memo:
        return memo[cid]
    out: set[str] = set()
    for p in pm.get(cid, []):
        out.add(p)
        out |= ancestors(p, pm, memo)
    memo[cid] = out
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dup-min", type=float, default=86.0)
    ap.add_argument("--syn-min", type=float, default=92.0)
    ap.add_argument("--mis-min-alt", type=float, default=82.0)
    ap.add_argument("--mis-min-delta", type=float, default=12.0)
    ap.add_argument("--limit", type=int, default=40)
    args = ap.parse_args()

    data = yaml.safe_load(YAML_PATH.read_text())
    concepts = data["concepts"]
    by = {c["id"]: c for c in concepts}
    pm = {c["id"]: list(c.get("parents") or []) for c in concepts}
    memo: dict[str, set[str]] = {}

    antonym_edges: set[tuple[str, str]] = set()
    for c in concepts:
        for a in c.get("antonyms") or []:
            antonym_edges.add(tuple(sorted((c["id"], a))))

    def is_antonym_pair(a: str, b: str) -> bool:
        return tuple(sorted((a, b))) in antonym_edges

    print(f"engine={ENGINE}  concepts={len(concepts)}  antonym_pairs={len(antonym_edges)}")

    prefs = [(c["id"], c["preferred_label"], norm(c["preferred_label"])) for c in concepts]

    # Exact normalized collisions
    by_n: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for cid, lab, n in prefs:
        by_n[n].append((cid, lab))
    exact = {k: v for k, v in by_n.items() if len(v) > 1}
    print(f"\n=== Exact normalized label collisions: {len(exact)} ===")
    for n, items in sorted(exact.items()):
        print(f"  {n}: {items}")

    # Near-duplicate preferred labels
    dup_pairs: list[tuple] = []
    for i, (ida, ra, na) in enumerate(prefs):
        for idb, rb, nb in prefs[i + 1 :]:
            score = 100.0 if na == nb else max(fuzz.ratio(na, nb), fuzz.token_sort_ratio(na, nb))
            if score < args.dup_min:
                continue
            if is_antonym_pair(ida, idb):
                continue
            anc_a, anc_b = ancestors(ida, pm, memo), ancestors(idb, pm, memo)
            related = ida in anc_b or idb in anc_a
            same_parent = bool(set(pm.get(ida, [])) & set(pm.get(idb, [])))
            dup_pairs.append((score, ida, ra, idb, rb, related, same_parent))
    dup_pairs.sort(reverse=True)
    print(f"\n=== Near-duplicate preferred labels (≥{args.dup_min}): {len(dup_pairs)} ===")
    for score, ida, ra, idb, rb, related, same_parent in dup_pairs[: args.limit]:
        flags = []
        if related:
            flags.append("ancestry")
        if same_parent:
            flags.append("siblings")
        if not flags:
            flags.append("UNRELATED")
        print(f"{score:5.1f}  {ra} ({ida})")
        print(f"       {rb} ({idb})  [{', '.join(flags)}]")

    # Pref ≈ other synonym
    syn_hits: list[tuple] = []
    for ida, ra, na in prefs:
        for c in concepts:
            if c["id"] == ida:
                continue
            for syn in c.get("synonyms") or []:
                nb = norm(syn)
                score = max(fuzz.ratio(na, nb), fuzz.token_sort_ratio(na, nb))
                if score >= args.syn_min:
                    syn_hits.append((score, ida, ra, c["id"], syn, c["preferred_label"]))
    syn_hits.sort(reverse=True)
    seen: set[tuple[str, str]] = set()
    uniq: list[tuple] = []
    for h in syn_hits:
        key = tuple(sorted((h[1], h[3])))
        if key in seen:
            continue
        seen.add(key)
        uniq.append(h)
    print(f"\n=== Pref ≈ other synonym (≥{args.syn_min}): {len(uniq)} ===")
    for score, ida, ra, idb, syn, pref in uniq[: args.limit]:
        print(f'{score:5.1f}  pref {ra} ({ida}) ≈ syn of {pref} ({idb}): "{syn}"')

    # Misparenting heuristic
    mis: list[tuple] = []
    for c in concepts:
        cid = c["id"]
        parents = pm.get(cid, [])
        if not parents:
            continue
        cn = norm(c["preferred_label"])
        for p in parents:
            if p not in by:
                continue
            pn = norm(by[p]["preferred_label"])
            parent_score = max(
                fuzz.ratio(cn, pn), fuzz.partial_ratio(cn, pn), fuzz.token_sort_ratio(cn, pn)
            )
            best: tuple[float, str, str] | None = None
            for o in concepts:
                oid = o["id"]
                if oid in (cid, p):
                    continue
                if oid in ancestors(cid, pm, memo) or cid in ancestors(oid, pm, memo):
                    continue
                on = norm(o["preferred_label"])
                sc = max(fuzz.ratio(cn, on), fuzz.token_sort_ratio(cn, on))
                if sc < args.mis_min_alt:
                    continue
                if is_antonym_pair(cid, oid):
                    continue
                if best is None or sc > best[0]:
                    best = (sc, oid, o["preferred_label"])
            if best and best[0] >= parent_score + args.mis_min_delta:
                mis.append(
                    (
                        best[0] - parent_score,
                        best[0],
                        parent_score,
                        cid,
                        c["preferred_label"],
                        p,
                        by[p]["preferred_label"],
                        best[1],
                        best[2],
                    )
                )
    mis.sort(reverse=True)
    print(
        f"\n=== Possible misparenting (alt−parent≥{args.mis_min_delta}, alt≥{args.mis_min_alt}): "
        f"{len(mis)} ==="
    )
    for delta, alt_sc, par_sc, cid, clab, pid, plab, aid, alab in mis[: args.limit]:
        print(f"+{delta:4.1f}  {clab} ({cid})")
        print(f"       parent {plab} ({pid}) score={par_sc:.0f}")
        print(f"       closer {alab} ({aid}) score={alt_sc:.0f}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
