#!/usr/bin/env python3
"""Extract reaction types and annotations from AMD Accelrys parquet tables.

Reads under data/amd/:
  rxn.pq  enz.pq  ctx.pq  mol.pq  litref.pq  (lit.pq / ind.pq unused here)

Writes under data/derived/db_extracts/amd/ (committed; raw parquet stays local):
  counts_*.tsv          — term frequencies per annotation field
  counts_summary.json   — row counts and unique-term tallies
  examples_by_term.tsv  — up to N examples per RXNCLASS term
  examples.tsv          — full row dump only with --write-examples (large)

Usage:
  uv run python crates/xenosite-tagger/tools/extract_amd.py
  uv run python crates/xenosite-tagger/tools/extract_amd.py --examples-per-term 5
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
DEFAULT_AMD = REPO / "data" / "amd"
DEFAULT_OUT = REPO / "data" / "derived" / "db_extracts" / "amd"


def write_counts(path: Path, counter: Counter[str], *, field: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n")
        w.writerow(["term", "count", "field"])
        for term, count in counter.most_common():
            w.writerow([term, count, field])


def _join(values: list[str] | None, sep: str = " | ") -> str:
    if not values:
        return ""
    return sep.join(values)


def _as_list(value: object) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def extract(
    amd_dir: Path,
    out_dir: Path,
    examples_per_term: int,
    *,
    write_examples: bool = False,
) -> None:
    try:
        import pyarrow.parquet as pq
    except ImportError as exc:  # pragma: no cover
        raise SystemExit(
            "pyarrow is required (uv sync --group dev, or uv add --dev pyarrow)"
        ) from exc

    t0 = time.perf_counter()
    print(f"[amd] loading tables from {amd_dir}", flush=True)
    rxn = pq.read_table(amd_dir / "rxn.pq")
    enz = pq.read_table(amd_dir / "enz.pq")
    ctx = pq.read_table(amd_dir / "ctx.pq")
    mol = pq.read_table(amd_dir / "mol.pq")
    print(
        f"[amd] rows: rxn={rxn.num_rows} enz={enz.num_rows} "
        f"ctx={ctx.num_rows} mol={mol.num_rows}",
        flush=True,
    )

    # molregno -> smiles / symbol
    mol_smiles: dict[int, str] = {}
    mol_symbol: dict[int, str] = {}
    activity: Counter[str] = Counter()
    cmpdclass: Counter[str] = Counter()
    for i in range(mol.num_rows):
        mrn = mol.column("MOLREGNO")[i].as_py()
        smiles = mol.column("MOLSTRUCTURE")[i].as_py() or ""
        symbols = _as_list(mol.column("SYMBOL")[i].as_py())
        mol_smiles[mrn] = smiles
        mol_symbol[mrn] = symbols[0] if symbols else ""
        acts = _as_list(mol.column("ACTIVITY")[i].as_py())
        classes = _as_list(mol.column("CMPDCLASS")[i].as_py())
        if acts:
            for a in acts:
                if a:
                    activity[str(a)] += 1
        else:
            activity["(empty)"] += 1
        if classes:
            for c in classes:
                if c:
                    cmpdclass[str(c)] += 1
        else:
            cmpdclass["(empty)"] += 1
    print(f"[amd] indexed {len(mol_smiles)} molecules", flush=True)

    # LITREFREGNO -> enzyme names / species / route / conjugates
    enz_by_lit: dict[int, list[str]] = defaultdict(list)
    for i in range(enz.num_rows):
        lit = enz.column("LITREFREGNO")[i].as_py()
        name = enz.column("ENZ_NAME")[i].as_py()
        iso = enz.column("ISOENZYME")[i].as_py()
        if lit is None or not name:
            continue
        label = str(name) if not iso else f"{name} ({iso})"
        enz_by_lit[lit].append(label)

    # Raw enzyme name counts from enz table (one row per litref annotation)
    enzyme_token: Counter[str] = Counter()
    for i in range(enz.num_rows):
        name = enz.column("ENZ_NAME")[i].as_py()
        enzyme_token[str(name) if name else "(empty)"] += 1

    species_c: Counter[str] = Counter()
    route_c: Counter[str] = Counter()
    conjugates_c: Counter[str] = Counter()
    excretion_c: Counter[str] = Counter()
    covalent_c: Counter[str] = Counter()
    polymorph_c: Counter[str] = Counter()
    species_by_lit: dict[int, list[str]] = defaultdict(list)
    route_by_lit: dict[int, list[str]] = defaultdict(list)
    conj_by_lit: dict[int, list[str]] = defaultdict(list)
    excret_by_lit: dict[int, list[str]] = defaultdict(list)

    for i in range(ctx.num_rows):
        lit = ctx.column("LITREFREGNO")[i].as_py()
        for col, counter, by_lit in (
            ("SPECIES", species_c, species_by_lit),
            ("ROUTE", route_c, route_by_lit),
            ("CONJUGATES", conjugates_c, conj_by_lit),
            ("EXCRETION", excretion_c, excret_by_lit),
        ):
            v = ctx.column(col)[i].as_py()
            key = "(null)" if v is None or v == "" else str(v)
            counter[key] += 1
            if lit is not None and key != "(null)":
                by_lit[lit].append(key)
        cob = ctx.column("COVALENT_BDG")[i].as_py()
        covalent_c["(null)" if cob is None else str(cob)] += 1
        poly = ctx.column("POLYMORPH")[i].as_py()
        polymorph_c["(null)" if poly is None else str(poly)] += 1

    print(f"[amd] indexed ctx/enz for {len(enz_by_lit)} litrefs with enzymes", flush=True)

    rxnclass: Counter[str] = Counter()
    rxnclass_combo: Counter[str] = Counter()
    step_c: Counter[str] = Counter()
    schemeid_c: Counter[str] = Counter()

    example_cols = [
        "rxnregno",
        "schemeid",
        "rxnclass",
        "step",
        "path",
        "reactant_molregno",
        "product_molregno",
        "reactant_symbol",
        "product_symbol",
        "reactant_smiles",
        "product_smiles",
        "enzymes",
        "species",
        "routes",
        "conjugates",
        "excretion",
        "n_litrefs",
    ]
    out_dir.mkdir(parents=True, exist_ok=True)
    examples_fh = None
    examples_w = None
    if write_examples:
        examples_fh = (out_dir / "examples.tsv").open("w", newline="")
        examples_w = csv.DictWriter(
            examples_fh, fieldnames=example_cols, delimiter="\t", lineterminator="\n"
        )
        examples_w.writeheader()

    by_term: dict[str, list[dict[str, str]]] = defaultdict(list)
    n_rxn = rxn.num_rows
    report_every = max(10_000, n_rxn // 20)

    for i in range(n_rxn):
        if i > 0 and i % report_every == 0:
            elapsed = time.perf_counter() - t0
            print(f"[amd] reactions {i}/{n_rxn} ({elapsed:.1f}s)", flush=True)

        classes = [str(x) for x in _as_list(rxn.column("RXNCLASS")[i].as_py()) if x]
        steps = [str(x) for x in _as_list(rxn.column("STEP")[i].as_py()) if x]
        paths = [str(x) for x in _as_list(rxn.column("PATH")[i].as_py()) if x]
        litrefs = [int(x) for x in _as_list(rxn.column("LITREFREGNO")[i].as_py()) if x is not None]
        scheme = rxn.column("SCHEMEID")[i].as_py()
        scheme_s = "" if scheme is None else str(scheme)
        if scheme_s:
            schemeid_c[scheme_s] += 1
        else:
            schemeid_c["(empty)"] += 1

        if classes:
            rxnclass_combo[" | ".join(classes)] += 1
            for c in classes:
                rxnclass[c] += 1
        else:
            rxnclass["(empty)"] += 1
            rxnclass_combo["(empty)"] += 1

        if steps:
            for s in steps:
                step_c[s] += 1
        else:
            step_c["(empty)"] += 1

        reactant = rxn.column("REACTANT")[i].as_py()
        product = rxn.column("PRODUCT")[i].as_py()
        r_smiles = mol_smiles.get(reactant, "") if reactant is not None else ""
        p_smiles = mol_smiles.get(product, "") if product is not None else ""
        r_sym = mol_symbol.get(reactant, "") if reactant is not None else ""
        p_sym = mol_symbol.get(product, "") if product is not None else ""

        enz_names: list[str] = []
        species: list[str] = []
        routes: list[str] = []
        conjugates: list[str] = []
        excretion: list[str] = []
        seen_e: set[str] = set()
        seen_s: set[str] = set()
        seen_r: set[str] = set()
        seen_c: set[str] = set()
        seen_x: set[str] = set()
        for lit in litrefs:
            for n in enz_by_lit.get(lit, []):
                if n not in seen_e:
                    seen_e.add(n)
                    enz_names.append(n)
            for n in species_by_lit.get(lit, []):
                if n not in seen_s:
                    seen_s.add(n)
                    species.append(n)
            for n in route_by_lit.get(lit, []):
                if n not in seen_r:
                    seen_r.add(n)
                    routes.append(n)
            for n in conj_by_lit.get(lit, []):
                if n not in seen_c:
                    seen_c.add(n)
                    conjugates.append(n)
            for n in excret_by_lit.get(lit, []):
                if n not in seen_x:
                    seen_x.add(n)
                    excretion.append(n)

        row = {
            "rxnregno": str(rxn.column("RXNREGNO")[i].as_py()),
            "schemeid": scheme_s,
            "rxnclass": " | ".join(classes),
            "step": " | ".join(steps),
            "path": " | ".join(paths),
            "reactant_molregno": "" if reactant is None else str(reactant),
            "product_molregno": "" if product is None else str(product),
            "reactant_symbol": r_sym,
            "product_symbol": p_sym,
            "reactant_smiles": r_smiles,
            "product_smiles": p_smiles,
            "enzymes": _join(enz_names),
            "species": _join(species),
            "routes": _join(routes),
            "conjugates": _join(conjugates),
            "excretion": _join(excretion),
            "n_litrefs": str(len(litrefs)),
        }
        if examples_w is not None:
            examples_w.writerow(row)

        for c in classes:
            if len(by_term[c]) < examples_per_term:
                by_term[c].append(row)

    if examples_fh is not None:
        examples_fh.close()
        print(f"[amd] wrote examples ({n_rxn} rows)", flush=True)

    write_counts(out_dir / "counts_rxnclass.tsv", rxnclass, field="RXNCLASS")
    write_counts(
        out_dir / "counts_rxnclass_combo.tsv", rxnclass_combo, field="RXNCLASS combo"
    )
    write_counts(out_dir / "counts_step.tsv", step_c, field="STEP")
    write_counts(out_dir / "counts_schemeid.tsv", schemeid_c, field="SCHEMEID")
    write_counts(out_dir / "counts_enzyme.tsv", enzyme_token, field="ENZ_NAME")
    write_counts(out_dir / "counts_species.tsv", species_c, field="SPECIES")
    write_counts(out_dir / "counts_route.tsv", route_c, field="ROUTE")
    write_counts(out_dir / "counts_conjugates.tsv", conjugates_c, field="CONJUGATES")
    write_counts(out_dir / "counts_excretion.tsv", excretion_c, field="EXCRETION")
    write_counts(out_dir / "counts_covalent_bdg.tsv", covalent_c, field="COVALENT_BDG")
    write_counts(out_dir / "counts_polymorph.tsv", polymorph_c, field="POLYMORPH")
    write_counts(out_dir / "counts_activity.tsv", activity, field="ACTIVITY")
    write_counts(out_dir / "counts_cmpdclass.tsv", cmpdclass, field="CMPDCLASS")

    with (out_dir / "examples_by_term.tsv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=example_cols, delimiter="\t", lineterminator="\n")
        w.writeheader()
        for term, _ in rxnclass.most_common():
            if term == "(empty)":
                continue
            for row in by_term.get(term, []):
                w.writerow(row)

    summary = {
        "source": str(amd_dir.relative_to(REPO)) if amd_dir.is_relative_to(REPO) else str(amd_dir),
        "n_reactions": n_rxn,
        "n_molecules": len(mol_smiles),
        "n_unique": {
            "RXNCLASS": len(rxnclass),
            "RXNCLASS combo": len(rxnclass_combo),
            "STEP": len(step_c),
            "SCHEMEID": len(schemeid_c),
            "ENZ_NAME": len(enzyme_token),
            "SPECIES": len(species_c),
            "ROUTE": len(route_c),
            "CONJUGATES": len(conjugates_c),
            "EXCRETION": len(excretion_c),
            "ACTIVITY": len(activity),
            "CMPDCLASS": len(cmpdclass),
        },
        "top_rxnclass": rxnclass.most_common(30),
        "top_enzymes": enzyme_token.most_common(25),
        "top_species": species_c.most_common(15),
        "elapsed_s": round(time.perf_counter() - t0, 2),
        "outputs": sorted(p.name for p in out_dir.iterdir() if p.is_file()),
    }
    (out_dir / "counts_summary.json").write_text(json.dumps(summary, indent=2) + "\n")

    print(f"[amd] wrote {out_dir} in {summary['elapsed_s']}s", flush=True)
    print(f"[amd] RXNCLASS terms: {len(rxnclass)}", flush=True)
    print(
        f"[amd] examples_by_term (cap {examples_per_term}/term): "
        f"{sum(len(v) for k, v in by_term.items() if k != '(empty)')}",
        flush=True,
    )


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--amd-dir", type=Path, default=DEFAULT_AMD)
    p.add_argument("--out", type=Path, default=DEFAULT_OUT)
    p.add_argument(
        "--examples-per-term",
        type=int,
        default=5,
        help="Max examples kept per RXNCLASS in examples_by_term.tsv",
    )
    p.add_argument(
        "--write-examples",
        action="store_true",
        help="Also write full examples.tsv (large; keep under artifacts/ locally)",
    )
    args = p.parse_args(argv)
    if not (args.amd_dir / "rxn.pq").exists():
        print(f"error: missing {args.amd_dir / 'rxn.pq'}", file=sys.stderr)
        return 1
    extract(
        args.amd_dir,
        args.out,
        args.examples_per_term,
        write_examples=args.write_examples,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
