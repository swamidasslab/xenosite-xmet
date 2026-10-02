#!/usr/bin/env python3
"""Review edit patches: what they change, and how spec and quality checks move.

Spec findings come from ``xenosite.xmet.validate``; quality notes come from the
site generator's checks (``site.config.yaml``). Both are compared with the
current ontology, so the report lists what a patch fixes and what it introduces.

  uv run python tools/patch_review.py data/patches/pending/my-edit.yaml [--out review.md]

Exit status: 1 if the patches do not apply, add spec failures, or add quality errors; else 0.
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from sitegen.config import Config  # noqa: E402
from sitegen.model import Vocabulary  # noqa: E402
from sitegen.quality import REF_RE as REF  # noqa: E402
from sitegen.quality import run_checks  # noqa: E402

from xenosite.xmet.edits import (  # noqa: E402
    PatchError,
    format_review,
    load_patch,
    render,
    review,
)


def quality_flags(cfg: Config, source: Path) -> dict[tuple[str, str, str], str]:
    """(concept, check, detail) → readable line, for the vocabulary at ``source``."""
    cfg.data["vocabulary"]["source"] = str(source)
    v = Vocabulary(cfg)
    run_checks(v)
    out = {}
    for slug, c in v.concepts.items():
        for f in c["flags"]:
            detail = REF.sub(lambda m: f"{v.concepts[m[1]]['label']} ({v.concepts[m[1]]['curie']})" if m[1] in v.concepts else m[1], f["detail"])
            out[(c["curie"], f["check"], f["detail"])] = (
                f"[{f['severity']}] {f['check'].replace('_', ' ')}: {c['curie']} “{c['label']}”" + (f" — {detail}" if detail else "")
            )
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("patches", nargs="+")
    ap.add_argument("--config", default=str(ROOT / "site.config.yaml"))
    ap.add_argument("--out", help="also write the markdown report here")
    args = ap.parse_args()

    try:
        patches = [load_patch(p) for p in args.patches]
    except PatchError as e:
        report = "### Patch review\n\n**❌ Malformed patch:**\n" + "\n".join(f"- {x}" for x in e.problems)
        print(report)
        if args.out:
            Path(args.out).write_text(report)
        return 1

    rv = review(patches)
    extra = []
    if rv.workspace is not None:
        cfg = Config(Path(args.config))
        before = quality_flags(cfg, cfg.resolve(cfg.vocab["source"]))  # type: ignore[arg-type]
        with tempfile.TemporaryDirectory() as tmp:
            patched = Path(tmp) / "xmet.yaml"
            patched.write_text(render(rv.workspace))
            after = quality_flags(Config(Path(args.config)), patched)
        fixed = [before[k] for k in before.keys() - after.keys()]
        new = [after[k] for k in after.keys() - before.keys()]
        extra.append(("Quality notes", sorted(fixed), sorted(new), len(before.keys() & after.keys())))

    report = format_review(rv, extra)
    print(report)
    if args.out:
        Path(args.out).write_text(report)
    new_quality_errors = any(line.startswith("[error]") for _, _, new, _ in extra for line in new)
    return 0 if rv.ok and not new_quality_errors else 1


if __name__ == "__main__":
    sys.exit(main())
