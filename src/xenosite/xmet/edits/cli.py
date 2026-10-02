"""``xmet-edit`` — check and apply XMET edit patches.

    xmet-edit check data/patches/pending/my-edit.yaml     # diff + validation vs current
    xmet-edit apply data/patches/pending/*.yaml           # write xmet.yaml, archive patches
    xmet-edit list                                        # pending patches

Exit status: 0 when the patches apply and introduce no new spec failures, else 1.
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path

import yaml

from xenosite.xmet.edits import (
    PatchError,
    Workspace,
    apply_patches,
    format_review,
    load_patch,
    review,
    write,
)
from xenosite.xmet.paths import data_dir

PENDING = data_dir() / "patches" / "pending"
APPLIED = data_dir() / "patches" / "applied"


def _load(paths: list[str]):
    patches, problems = [], []
    for p in paths:
        try:
            patches.append(load_patch(p))
        except PatchError as e:
            problems += [f"{p}: {x}" for x in e.problems]
        except (OSError, yaml.YAMLError) as e:
            problems.append(f"{p}: {e}")
    return patches, problems


def cmd_check(args: argparse.Namespace) -> int:
    patches, problems = _load(args.patches)
    if problems:
        print("\n".join(problems))
        return 1
    rv = review(patches)
    print(format_review(rv))
    return 0 if rv.ok else 1


def cmd_apply(args: argparse.Namespace) -> int:
    patches, problems = _load(args.patches)
    if problems:
        print("\n".join(problems))
        return 1
    rv = review(patches)
    if not rv.ok and not args.force:
        print(format_review(rv))
        print("\nNot applied (use --force to apply despite new findings).")
        return 1
    ws = Workspace.load()
    apply_patches(ws, patches)
    write(ws)
    if not args.keep:
        APPLIED.mkdir(parents=True, exist_ok=True)
        stamp = dt.date.today().isoformat()
        for p in patches:
            record = {**p.raw, "applied": {"date": stamp, "ids": {k: v for k, v in ws.ids.items()}}}
            (APPLIED / p.path.name).write_text(yaml.safe_dump(record, sort_keys=False, allow_unicode=True))
            if p.path.resolve().is_relative_to(PENDING.resolve()):
                p.path.unlink()
    print(format_review(rv))
    print("\nApplied. Next: `make ontology-export` and commit.")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    for path in sorted(Path(args.dir).glob("*.yaml")):
        try:
            p = load_patch(path)
            print(f"{path.name}\t{p.id}\t{len(p.changes)} change(s)\t{p.rationale.splitlines()[0] if p.rationale else ''}")
        except PatchError as e:
            print(f"{path.name}\tINVALID\t{e}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="xmet-edit", description="Check and apply XMET edit patches.")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("check", help="show what patches change and how validation moves")
    p.add_argument("patches", nargs="+")
    p.set_defaults(func=cmd_check)
    p = sub.add_parser("apply", help="apply patches to xmet.yaml and archive them")
    p.add_argument("patches", nargs="+")
    p.add_argument("--force", action="store_true", help="apply even if new spec findings appear")
    p.add_argument("--keep", action="store_true", help="leave patch files in place (no archive)")
    p.set_defaults(func=cmd_apply)
    p = sub.add_parser("list", help="list patches in a directory")
    p.add_argument("dir", nargs="?", default=str(PENDING))
    p.set_defaults(func=cmd_list)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
