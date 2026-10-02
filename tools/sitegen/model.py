"""Build the generic vocabulary model (concepts, hierarchy, relations) from a YAML source."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from .config import Config

FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?", re.S)


def read_frontmatter(path: Path) -> dict[str, Any]:
    m = FRONTMATTER_RE.match(path.read_text())
    return (yaml.safe_load(m.group(1)) or {}) if m else {}


def as_list(v: Any) -> list[Any]:
    if v is None:
        return []
    return v if isinstance(v, list) else [v]


class Vocabulary:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        src = cfg.resolve(cfg.vocab["source"])
        assert src is not None
        self.source_path = src
        text = src.read_text()
        doc = yaml.safe_load(text)
        self.scheme_raw: dict[str, Any] = doc.get(cfg.vocab.get("scheme_key", "scheme")) or {}
        self.raw: list[dict[str, Any]] = doc[cfg.vocab.get("concepts_key", "concepts")]
        self.lines = self._line_index(text)
        self.concepts: dict[str, dict[str, Any]] = {}
        self.dangling: list[tuple[str, str, str]] = []  # (slug, relation, target)
        self._build()

    # --- identifiers ---------------------------------------------------------

    def slug(self, curie: str) -> str | None:
        pre = self.cfg.prefix + ":"
        if curie.startswith(pre):
            return curie[len(pre):]
        if curie.startswith(self.cfg.namespace):
            return curie[len(self.cfg.namespace):]
        return None

    def iri(self, slug: str) -> str:
        return self.cfg.namespace + slug

    def external(self, curie: str) -> dict[str, str]:
        if curie.startswith(("http://", "https://")):
            return {"curie": curie, "iri": curie}
        pre, _, local = curie.partition(":")
        base = (self.cfg.vocab.get("external_prefixes") or {}).get(pre)
        return {"curie": curie, "iri": base + local if base else ""}

    def _line_index(self, text: str) -> dict[str, int]:
        id_key = self.cfg.field("id")
        pat = re.compile(rf"^\s*-\s*{re.escape(id_key)}:\s*['\"]?([^'\"\s]+)")
        out: dict[str, int] = {}
        for i, line in enumerate(text.splitlines(), 1):
            m = pat.match(line)
            if m:
                out.setdefault(m.group(1), i)
        return out

    # --- build ---------------------------------------------------------------

    def _build(self) -> None:
        f = self.cfg.field
        rel_cfg = self.cfg.relations
        core = {f("id"), f("label"), f("definition"), f("synonyms"), f("parents")}
        sidecar_dir = self.cfg.resolve(self.cfg.vocab.get("sidecars"))

        for c in self.raw:
            cid = c[f("id")]
            slug = self.slug(cid) or cid
            extras = {k: v for k, v in c.items() if k not in core and k not in rel_cfg}
            sidecar = sidecar_dir / f"{slug}.md" if sidecar_dir else None
            has_sidecar = bool(sidecar and sidecar.exists())
            if has_sidecar:
                assert sidecar is not None
                extras.update(read_frontmatter(sidecar))
            self.concepts[slug] = {
                "slug": slug,
                "curie": cid,
                "iri": self.iri(slug),
                "label": c.get(f("label")) or slug,
                "definition": c.get(f("definition")) or "",
                "synonyms": as_list(c.get(f("synonyms"))),
                "parents": [],
                "children": [],
                "relations": [],
                "extras": extras,
                "has_sidecar": has_sidecar,
                "source_line": self.lines.get(cid),
                "_raw": c,
            }

        for slug, c in self.concepts.items():
            for p in as_list(c["_raw"].get(f("parents"))):
                ps = self.slug(p)
                if ps in self.concepts:
                    c["parents"].append(ps)
                    self.concepts[ps]["children"].append(slug)
                else:
                    self.dangling.append((slug, "parent", p))

        self._relations()
        self._hierarchy()
        for c in self.concepts.values():
            c["children"].sort(key=lambda s: self.concepts[s]["label"].lower())
            del c["_raw"]

    def _relations(self) -> None:
        rel_cfg = self.cfg.relations
        outgoing: dict[str, dict[str, list[str]]] = {s: {} for s in self.concepts}
        for slug, c in self.concepts.items():
            for key, rc in rel_cfg.items():
                for target in as_list(c["_raw"].get(key)):
                    ts = self.slug(str(target))
                    if rc.get("external") or ts is None:
                        c["relations"].append(
                            {"key": key, "direction": "out", "external": True, **self.external(str(target))}
                        )
                    elif ts in self.concepts:
                        outgoing[slug].setdefault(key, []).append(ts)
                        c["relations"].append({"key": key, "direction": "out", "target": ts})
                    else:
                        self.dangling.append((slug, key, str(target)))

        # Incoming links: symmetric relations and declared inverses are shown as implied
        # links of the same/inverse type; others under the relation's inverse label.
        for src, rels in outgoing.items():
            for key, targets in rels.items():
                rc = rel_cfg[key]
                for t in targets:
                    if rc.get("symmetric"):
                        k, direction = key, "out"
                    elif rc.get("inverse") in rel_cfg:
                        k, direction = rc["inverse"], "out"
                    else:
                        k, direction = key, "in"
                    if direction == "out" and src in outgoing[t].get(k, []):
                        continue  # already stated on the target
                    self.concepts[t]["relations"].append(
                        {"key": k, "direction": direction, "target": src, "implied": direction == "out"}
                    )
        self.outgoing = outgoing

    def _hierarchy(self) -> None:
        self.roots = sorted(
            (s for s, c in self.concepts.items() if not c["parents"]),
            key=lambda s: self.concepts[s]["label"].lower(),
        )
        self.cycles: list[str] = []
        for slug, c in self.concepts.items():
            path, seen, cur = [], {slug}, c
            while cur["parents"]:
                p = cur["parents"][0]
                if p in seen:
                    self.cycles.append(slug)
                    break
                seen.add(p)
                path.append(p)
                cur = self.concepts[p]
            c["ancestors"] = list(reversed(path))
            c["depth"] = len(path)

        def count(s: str, stack: frozenset[str] = frozenset()) -> int:
            if s in stack:
                return 0
            kids = self.concepts[s]["children"]
            return len(kids) + sum(count(k, stack | {s}) for k in kids)

        for slug, c in self.concepts.items():
            c["descendants"] = count(slug)

    def scheme(self) -> dict[str, Any]:
        f = self.cfg.field
        return {
            "iri": self.cfg.vocab.get("scheme_iri") or self.cfg.namespace,
            "label": self.scheme_raw.get(f("label")) or self.cfg.site.get("title", ""),
            "definition": self.scheme_raw.get(f("definition")) or "",
        }
