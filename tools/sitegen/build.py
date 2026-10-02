#!/usr/bin/env python3
"""Generate the data contract and static assets for the vocabulary site.

Reads a site config (default: site.config.yaml at the repo root) and writes:

  site/src/generated/vocab.json   data contract consumed by the Astro site
  site/public/term/<slug>.ttl     per-term Turtle   (if the config names an RDF graph)
  site/public/term/<slug>.jsonld  per-term JSON-LD
  site/public/downloads/*         whole-vocabulary downloads listed in the config
  site/public/assets/logo.*       site logo
  <resolver.output>               w3id-style .htaccess

Usage:
  uv run python tools/sitegen/build.py [--config site.config.yaml] [--site site] [--no-rdf]
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    __package__ = "sitegen"

from .config import Config  # noqa: E402
from .model import Vocabulary  # noqa: E402
from .quality import run_checks  # noqa: E402
from .rdf import write_term_rdf  # noqa: E402
from .resolver import htaccess  # noqa: E402

CONTRACT_VERSION = 1


def load_mappings(cfg: Config, v: Vocabulary) -> dict[str, Any]:
    sec = cfg.section("mappings")
    by_slug: dict[str, list[dict[str, str]]] = {}
    sources = []
    for src in sec.get("sources") or []:
        path = cfg.resolve(src["path"])
        if not path or not path.exists():
            continue
        lines = [ln for ln in path.read_text().splitlines() if ln and not ln.startswith("#")]
        n = 0
        for row in csv.DictReader(lines, delimiter="\t"):
            slug = v.slug(row.get("subject_id", ""))
            if slug not in v.concepts:
                continue
            by_slug.setdefault(slug, []).append(
                {
                    "source": src["label"],
                    "predicate": row.get("predicate_id", ""),
                    "object": row.get("object_id", ""),
                    "object_label": row.get("object_label", ""),
                    "justification": row.get("mapping_justification", ""),
                }
            )
            n += 1
        sources.append({"label": src["label"], "path": src["path"], "count": n})
    for slug, c in v.concepts.items():
        c["mappings"] = by_slug.get(slug, [])
    return {"show": bool(sec.get("show")), "sources": sources}


def stats(v: Vocabulary, checks: list[dict[str, Any]]) -> dict[str, Any]:
    cs = v.concepts.values()
    by_sev: dict[str, int] = {}
    for c in cs:
        for sev in {f["severity"] for f in c["flags"]}:
            by_sev[sev] = by_sev.get(sev, 0) + 1
    return {
        "concepts": len(v.concepts),
        "synonyms": sum(len(c["synonyms"]) for c in cs),
        "relations": sum(1 for c in cs for r in c["relations"] if r["direction"] == "out" and not r.get("implied")),
        "roots": len(v.roots),
        "leaves": sum(1 for c in cs if not c["children"]),
        "max_depth": max((c["depth"] for c in cs), default=0),
        "flagged": sum(1 for c in cs if c["flags"]),
        "flagged_by_severity": by_sev,
        "checks": len(checks),
    }


def git_revision(root: Path) -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=root, text=True).strip()
    except Exception:
        return ""


def copy_assets(cfg: Config, public: Path) -> dict[str, Any]:
    out: dict[str, Any] = {"downloads": []}
    dl_dir = public / "downloads"
    shutil.rmtree(dl_dir, ignore_errors=True)
    dl_dir.mkdir(parents=True)
    for d in cfg.vocab.get("downloads") or []:
        src = cfg.resolve(d["path"])
        if src and src.exists():
            shutil.copy2(src, dl_dir / src.name)
            out["downloads"].append(
                {"label": d["label"], "file": src.name, "source": d["path"], "bytes": src.stat().st_size}
            )
    logo = cfg.resolve(cfg.site.get("logo"))
    if logo and logo.exists():
        (public / "assets").mkdir(parents=True, exist_ok=True)
        shutil.copy2(logo, public / "assets" / f"logo{logo.suffix}")
        out["logo"] = f"assets/logo{logo.suffix}"
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--config", default="site.config.yaml")
    ap.add_argument("--site", default="site", help="site directory (Astro project)")
    ap.add_argument("--no-rdf", action="store_true", help="skip per-term RDF (no rdflib needed)")
    args = ap.parse_args()

    cfg = Config(Path(args.config))
    site_dir = (cfg.root / args.site).resolve()
    public = site_dir / "public"

    v = Vocabulary(cfg)
    checks = run_checks(v)
    mappings = load_mappings(cfg, v)
    assets = copy_assets(cfg, public)

    term_dir = public / "term"
    shutil.rmtree(term_dir, ignore_errors=True)
    n_rdf = 0 if args.no_rdf else write_term_rdf(v, term_dir)

    content = cfg.section("content")
    repo = cfg.site.get("repo") or {}
    contract = {
        "version": CONTRACT_VERSION,
        "generated": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "revision": git_revision(cfg.root),
        "site": {
            **{k: v_ for k, v_ in cfg.site.items() if k not in ("logo", "repo")},
            "url": cfg.site_url,
            "base": cfg.base_path,
            "logo": assets.get("logo"),
            "repo": repo,
        },
        "ui": cfg.section("ui"),
        "paths": {
            "root": str(cfg.root),
            "pages": str(cfg.resolve(content.get("pages")) or ""),
            "checks": str(cfg.resolve(content.get("checks")) or ""),
            "sidecars": str(cfg.resolve(cfg.vocab.get("sidecars")) or ""),
            "source": cfg.vocab["source"],
            "sidecars_rel": cfg.vocab.get("sidecars") or "",
            "pages_rel": content.get("pages") or "",
            "checks_rel": content.get("checks") or "",
        },
        "edits": cfg.section("edits"),
        "sidecar_template": (
            cfg.resolve(cfg.vocab.get("sidecar_template")).read_text()  # type: ignore[union-attr]
            if cfg.vocab.get("sidecar_template") and cfg.resolve(cfg.vocab["sidecar_template"]).exists()  # type: ignore[union-attr]
            else ""
        ),
        "scheme": v.scheme(),
        "namespace": cfg.namespace,
        "curie_prefix": cfg.prefix,
        "relations": [{"key": k, **rc} for k, rc in cfg.relations.items()],
        "extra_fields": cfg.vocab.get("extra_fields") or {},
        "checks": checks,
        "mappings": mappings,
        "downloads": assets["downloads"],
        "term_rdf": n_rdf > 0,
        "stats": stats(v, checks),
        "roots": v.roots,
        "concepts": v.concepts,
    }
    gen = site_dir / "src" / "generated"
    gen.mkdir(parents=True, exist_ok=True)
    (gen / "vocab.json").write_text(json.dumps(contract, ensure_ascii=False, indent=1))
    # Rendered Markdown embeds live values ({{stats.*}}, [[slug]] labels), so the
    # renderer's content cache is stale whenever the contract changes.
    for cache in (site_dir / ".astro" / "data-store.json", site_dir / "node_modules" / ".astro" / "data-store.json"):
        cache.unlink(missing_ok=True)

    out = cfg.resolve(cfg.section("resolver").get("output"))
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(htaccess(cfg, term_rdf=n_rdf > 0))

    s = contract["stats"]
    print(
        f"sitegen: {s['concepts']} concepts, {s['flagged']} flagged, "
        f"{n_rdf} term RDF files → {gen / 'vocab.json'}"
    )


if __name__ == "__main__":
    main()
