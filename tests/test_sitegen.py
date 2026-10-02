"""Site generator: data-contract integrity and separation of site code from project content."""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from sitegen.config import Config  # noqa: E402
from sitegen.model import Vocabulary  # noqa: E402
from sitegen.quality import CHECKS, run_checks  # noqa: E402
from sitegen.resolver import htaccess  # noqa: E402


@pytest.fixture(scope="module")
def cfg() -> Config:
    return Config(ROOT / "site.config.yaml")


@pytest.fixture(scope="module")
def vocab(cfg: Config) -> Vocabulary:
    v = Vocabulary(cfg)
    run_checks(v)
    return v


def test_every_concept_reaches_a_root(vocab: Vocabulary) -> None:
    assert vocab.roots, "no root concepts"
    assert not vocab.cycles
    for slug, c in vocab.concepts.items():
        chain = c["ancestors"]
        assert (chain[0] if chain else slug) in vocab.roots, slug
        for child, parent in zip([*chain[1:], slug], chain):
            assert vocab.concepts[child]["parents"][0] == parent


def test_children_mirror_parents(vocab: Vocabulary) -> None:
    for slug, c in vocab.concepts.items():
        for p in c["parents"]:
            assert slug in vocab.concepts[p]["children"]
        for k in c["children"]:
            assert slug in vocab.concepts[k]["parents"]


def test_relations_resolve(vocab: Vocabulary, cfg: Config) -> None:
    for c in vocab.concepts.values():
        for r in c["relations"]:
            assert r["key"] in cfg.relations
            if not r.get("external"):
                assert r["target"] in vocab.concepts


def test_iris_use_namespace(vocab: Vocabulary, cfg: Config) -> None:
    for slug, c in vocab.concepts.items():
        assert c["iri"] == cfg.namespace + slug
    ttl = cfg.resolve(cfg.vocab["rdf"])
    assert ttl and f"<{cfg.namespace}>" in ttl.read_text().split("\n\n", 1)[0]


def test_configured_checks_exist(cfg: Config) -> None:
    assert set(cfg.section("quality")["checks"]) <= set(CHECKS)


def test_check_explanations_exist(cfg: Config) -> None:
    checks_dir = cfg.resolve(cfg.section("content")["checks"])
    assert checks_dir
    for name in cfg.section("quality")["checks"]:
        assert (checks_dir / f"{name}.md").exists(), f"missing explanation for check {name}"


def test_resolver_routes_terms(cfg: Config) -> None:
    rules = htaccess(cfg, term_rdf=True)
    slug = cfg.section("resolver")["slug_pattern"]
    assert f"RewriteRule ^({slug})/?$ {cfg.site_url}/term/$1/ [R=303,L]" in rules
    assert "text/turtle" in rules and "application/ld\\+json" in rules


def test_site_code_is_generic(cfg: Config) -> None:
    """Project specifics belong in site.config.yaml and content/, not in the site code."""
    words = {cfg.prefix, cfg.site["title"]}
    words |= set(re.findall(r"[a-z]{4,}", cfg.namespace.split("//", 1)[1].split("/", 1)[1].lower()))
    words |= {w for w in re.findall(r"[a-z]{4,}", cfg.site["repo"]["url"].lower()) if w not in {"https", "github"}}
    pattern = re.compile("|".join(re.escape(w) for w in sorted(words)), re.I)
    code = [
        *(ROOT / "site/src").rglob("*.*"),
        ROOT / "site/astro.config.mjs",
        ROOT / "site/package.json",
        *(ROOT / "tools/sitegen").glob("*.py"),
    ]
    hits = [
        f"{p.relative_to(ROOT)}:{i}: {m.group(0)}"
        for p in code
        if "generated" not in p.parts
        for i, line in enumerate(p.read_text().splitlines(), 1)
        for m in [pattern.search(line)]
        if m
    ]
    assert not hits, "project-specific strings in generic code:\n" + "\n".join(hits)


def test_branch_scoped_check_options(cfg: Config) -> None:
    """skip_under drops a subtree; min_chars_under sets a per-branch threshold."""
    v = Vocabulary(cfg)
    checks = cfg.section("quality")["checks"]
    run_checks(v)
    skipped = set(checks["single_child"]["skip_under"])
    for c in v.concepts.values():
        branch = {v.concepts[a]["curie"] for a in c["ancestors"]} | {c["curie"]}
        if branch & skipped:
            assert not any(f["check"] == "single_child" for f in c["flags"]), c["curie"]
    (lg, n), = checks["short_definition"]["min_chars_under"].items()
    under = [c for c in v.concepts.values() if lg in {v.concepts[a]["curie"] for a in c["ancestors"]}]
    assert under and all(
        any(f["check"] == "short_definition" for f in c["flags"]) == (0 < len(c["definition"].strip()) < n) for c in under
    )
