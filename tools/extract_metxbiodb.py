#!/usr/bin/env python3
"""Extract reaction types and annotations from MetXBioDB.

Reads:
  data/MetXBioDB-1-0.json

Writes under data/derived/db_extracts/metxbiodb/ (committed; raw DB stays local):
  counts_*.tsv          — term frequencies per annotation field
  counts_summary.json   — row counts and unique-term tallies
  examples_by_term.tsv  — up to N examples per Reaction Type term
  examples.tsv          — full row dump only with --write-examples

Usage:
  uv run python crates/xenosite-tagger/tools/extract_metxbiodb.py
  uv run python crates/xenosite-tagger/tools/extract_metxbiodb.py --examples-per-term 5
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
DEFAULT_INPUT = REPO / "data" / "MetXBioDB-1-0.json"
DEFAULT_OUT = REPO / "data" / "derived" / "db_extracts" / "metxbiodb"

# Multi-value fields split on these separators
ENZYME_SEP = ";"


def _nullish(value: object) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and value.strip().upper() in {"", "NULL", "NONE", "NA"}:
        return True
    return False


def _mol_fields(mol: dict | None, prefix: str) -> dict[str, str]:
    mol = mol or {}
    return {
        f"{prefix}_name": "" if _nullish(mol.get("Name")) else str(mol["Name"]),
        f"{prefix}_inchikey": "" if _nullish(mol.get("InChIKey")) else str(mol["InChIKey"]),
        f"{prefix}_inchi": "" if _nullish(mol.get("InChI")) else str(mol["InChI"]),
        f"{prefix}_metxbiodb_id": (
            "" if _nullish(mol.get("METXBIODB_ID")) else str(mol["METXBIODB_ID"])
        ),
        f"{prefix}_pubchem_cid": (
            "" if _nullish(mol.get("PUBCHEM_CID")) else str(mol["PUBCHEM_CID"])
        ),
    }


def write_counts(path: Path, counter: Counter[str], *, field: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n")
        w.writerow(["term", "count", "field"])
        for term, count in counter.most_common():
            w.writerow([term, count, field])


def parse_enzymes(raw: str) -> list[str]:
    if _nullish(raw):
        return []
    return [p.strip() for p in str(raw).split(ENZYME_SEP) if p.strip()]


# Known source-DB spelling fixes applied when writing public extract terms
_TERM_SPELLING = (
    ("Thiohene", "Thiophene"),
    ("thiohene", "thiophene"),
)


def normalize_source_term(term: str) -> str:
    out = term
    for bad, good in _TERM_SPELLING:
        out = out.replace(bad, good)
    return out


def extract(
    input_path: Path,
    out_dir: Path,
    examples_per_term: int,
    *,
    write_examples: bool = False,
) -> None:
    print(f"[metxbiodb] loading {input_path}", flush=True)
    payload = json.loads(input_path.read_text())
    bts: dict[str, dict] = payload["biotransformations"]
    print(f"[metxbiodb] {len(bts)} biotransformations", flush=True)

    reaction_type: Counter[str] = Counter()
    biotransformation_type: Counter[str] = Counter()
    biosystem: Counter[str] = Counter()
    enzyme: Counter[str] = Counter()
    enzyme_combo: Counter[str] = Counter()  # full Enzyme(s) string as recorded

    examples: list[dict[str, str]] = []
    by_term: dict[str, list[dict[str, str]]] = defaultdict(list)

    for biot_id, rec in bts.items():
        rt_raw = (rec.get("Reaction Type") or "").strip() or "(empty)"
        rt = normalize_source_term(rt_raw) if rt_raw != "(empty)" else rt_raw
        btt = (rec.get("Biotransformation type") or "").strip() or "(empty)"
        bs = (rec.get("Biosystem") or "").strip() or "(empty)"
        enz_raw = rec.get("Enzyme(s)") or ""
        enzymes = parse_enzymes(enz_raw)

        reaction_type[rt] += 1
        biotransformation_type[btt] += 1
        biosystem[bs] += 1
        if enzymes:
            enzyme_combo["; ".join(enzymes)] += 1
            for e in enzymes:
                enzyme[e] += 1
        else:
            enzyme["(empty)"] += 1
            enzyme_combo["(empty)"] += 1

        substrate = rec.get("Substrate") or {}
        products = rec.get("Products") or []
        product_names = []
        product_keys = []
        product_ids = []
        for p in products:
            if not isinstance(p, dict):
                continue
            if not _nullish(p.get("Name")):
                product_names.append(str(p["Name"]))
            if not _nullish(p.get("InChIKey")):
                product_keys.append(str(p["InChIKey"]))
            if not _nullish(p.get("METXBIODB_ID")):
                product_ids.append(str(p["METXBIODB_ID"]))

        refs = rec.get("References") or []
        row = {
            "biot_id": biot_id,
            "btmrid": str(rec.get("BioTransformer Reaction ID (BTMRID)") or ""),
            "reaction_type": "" if rt == "(empty)" else rt,
            "reaction_type_source": "" if rt_raw == "(empty)" else rt_raw,
            "biotransformation_type": "" if btt == "(empty)" else btt,
            "biosystem": "" if bs == "(empty)" else bs,
            "enzymes": "; ".join(enzymes),
            "n_enzymes": str(len(enzymes)),
            **_mol_fields(substrate, "substrate"),
            "product_names": " | ".join(product_names),
            "product_inchikeys": " | ".join(product_keys),
            "product_metxbiodb_ids": " | ".join(product_ids),
            "n_products": str(len(products)),
            "n_references": str(len(refs) if isinstance(refs, list) else 0),
        }
        examples.append(row)
        if rt != "(empty)" and len(by_term[rt]) < examples_per_term:
            by_term[rt].append(row)

    out_dir.mkdir(parents=True, exist_ok=True)
    write_counts(out_dir / "counts_reaction_type.tsv", reaction_type, field="Reaction Type")
    write_counts(
        out_dir / "counts_biotransformation_type.tsv",
        biotransformation_type,
        field="Biotransformation type",
    )
    write_counts(out_dir / "counts_biosystem.tsv", biosystem, field="Biosystem")
    write_counts(out_dir / "counts_enzyme.tsv", enzyme, field="Enzyme(s) token")
    write_counts(
        out_dir / "counts_enzyme_combo.tsv",
        enzyme_combo,
        field="Enzyme(s) full",
    )

    example_cols = [
        "biot_id",
        "btmrid",
        "reaction_type",
        "reaction_type_source",
        "biotransformation_type",
        "biosystem",
        "enzymes",
        "n_enzymes",
        "substrate_name",
        "substrate_inchikey",
        "substrate_inchi",
        "substrate_metxbiodb_id",
        "substrate_pubchem_cid",
        "product_names",
        "product_inchikeys",
        "product_metxbiodb_ids",
        "n_products",
        "n_references",
    ]
    if write_examples:
        with (out_dir / "examples.tsv").open("w", newline="") as fh:
            w = csv.DictWriter(
                fh, fieldnames=example_cols, delimiter="\t", lineterminator="\n"
            )
            w.writeheader()
            w.writerows(examples)

    with (out_dir / "examples_by_term.tsv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=example_cols, delimiter="\t", lineterminator="\n")
        w.writeheader()
        for term, _ in reaction_type.most_common():
            for row in by_term.get(term, []):
                w.writerow(row)

    summary = {
        "source": str(input_path.relative_to(REPO)) if input_path.is_relative_to(REPO) else str(input_path),
        "n_biotransformations": len(bts),
        "n_unique": {
            "Reaction Type": len(reaction_type),
            "Biotransformation type": len(biotransformation_type),
            "Biosystem": len(biosystem),
            "Enzyme(s) token": len(enzyme),
            "Enzyme(s) full": len(enzyme_combo),
        },
        "top_reaction_types": reaction_type.most_common(25),
        "biotransformation_type": biotransformation_type.most_common(),
        "biosystem": biosystem.most_common(),
        "top_enzymes": enzyme.most_common(25),
        "outputs": sorted(p.name for p in out_dir.iterdir() if p.is_file()),
    }
    (out_dir / "counts_summary.json").write_text(json.dumps(summary, indent=2) + "\n")

    print(f"[metxbiodb] wrote {out_dir}", flush=True)
    print(f"[metxbiodb] reaction types: {len(reaction_type)}", flush=True)
    print(f"[metxbiodb] enzyme tokens: {len(enzyme)}", flush=True)
    if write_examples:
        print(f"[metxbiodb] examples: {len(examples)}", flush=True)
    print(f"[metxbiodb] examples_by_term (cap {examples_per_term}/term): "
          f"{sum(len(v) for v in by_term.values())}", flush=True)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    p.add_argument("--out", type=Path, default=DEFAULT_OUT)
    p.add_argument(
        "--examples-per-term",
        type=int,
        default=5,
        help="Max examples kept per Reaction Type in examples_by_term.tsv",
    )
    p.add_argument(
        "--write-examples",
        action="store_true",
        help="Also write full examples.tsv (large; keep under artifacts/ locally)",
    )
    args = p.parse_args(argv)
    if not args.input.exists():
        print(f"error: input not found: {args.input}", file=sys.stderr)
        return 1
    extract(
        args.input,
        args.out,
        args.examples_per_term,
        write_examples=args.write_examples,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
