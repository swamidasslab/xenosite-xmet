"""``xmet-validate`` — check XMET, or a repository that depends on it, against the XMET spec.

Examples (from a sibling repository)::

    xmet-validate forest crates/xenosite-forest/src/rules.rs
    xmet-validate tagger data/rules
    xmet-validate ontology --tagger-sssom build/xmet-tagger.sssom.tsv
    xmet-validate curies data/ src/
    xmet-validate all --forest-rules-rs … --tagger-rules-dir … --json

Exit status: 0 when every report passes, 1 when any has hard failures.
"""

from __future__ import annotations

import argparse
import sys

from xenosite.xmet.validate import (
    Report,
    sources,
    validate_curies,
    validate_forest,
    validate_ontology,
    validate_tagger,
)


def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--forest-sssom", metavar="TSV", help="candidate Forest SSSOM to check in place of XMET's")
    common.add_argument("--tagger-sssom", metavar="TSV", help="candidate tagger SSSOM to check in place of XMET's")
    common.add_argument("--json", action="store_true", help="print machine-readable reports")

    parser = argparse.ArgumentParser(
        prog="xmet-validate",
        description="Check XMET, or a repository that depends on it, against the XMET spec.",
        epilog="Run `xmet-validate COMMAND -h` for command options.",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("ontology", parents=[common], help="XMET spec checks (hierarchy, relations, SSSOM discipline)")
    p = sub.add_parser("forest", parents=[common], help="Forest rules.rs vs XMET Forest SSSOM")
    p.add_argument("rules_rs", help="path to Forest src/rules.rs")
    p = sub.add_parser("tagger", parents=[common], help="tagger rules directory vs XMET tagger SSSOM")
    p.add_argument("rules_dir", help="directory holding the tagger *.rules.yaml files")
    p = sub.add_parser("curies", parents=[common], help="xmet: CURIEs in files are live concepts")
    p.add_argument("paths", nargs="+", help="files or directories to scan")
    p = sub.add_parser("all", parents=[common], help="ontology plus any sibling checks given")
    p.add_argument("--forest-rules-rs", metavar="PATH")
    p.add_argument("--tagger-rules-dir", metavar="PATH")
    p.add_argument("--curies", nargs="+", metavar="PATH", default=[])
    return parser


def run(args: argparse.Namespace) -> list[Report]:
    with sources(forest_sssom=args.forest_sssom, tagger_sssom=args.tagger_sssom):
        if args.command == "ontology":
            return [validate_ontology()]
        if args.command == "forest":
            return [validate_forest(args.rules_rs)]
        if args.command == "tagger":
            return [validate_tagger(args.rules_dir)]
        if args.command == "curies":
            return [validate_curies(args.paths)]
        reports = [validate_ontology()]
        if args.forest_rules_rs:
            reports.append(validate_forest(args.forest_rules_rs))
        if args.tagger_rules_dir:
            reports.append(validate_tagger(args.tagger_rules_dir))
        if args.curies:
            reports.append(validate_curies(args.curies))
        return reports


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    reports = run(args)
    if args.json:
        import json

        print(json.dumps([r.to_dict() for r in reports], indent=2, ensure_ascii=False))
    else:
        print("\n\n".join(r.text() for r in reports))
    return 0 if all(r.ok for r in reports) else 1


if __name__ == "__main__":
    sys.exit(main())
