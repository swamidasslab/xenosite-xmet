"""Structured edit proposals ("patches") for the XMET ontology.

A patch is one atomic changeset: an ordered list of operations applied
all-or-nothing and validated only in its final state, so a coherent multi-step
edit (retire a concept, mint its replacement, move the children) is reviewed as
one unit. Guards (``expect`` / ``from``) make a patch fail cleanly when its base
has changed. New concepts use placeholder refs (``new:<name>``) and receive real
``xmet:`` ids only when applied.

Applying a patch rewrites only the concepts it changes; every other concept
keeps its exact text in ``xmet.yaml``.

The same functions back ``xmet-edit``, the review bot, and XMET's tests.
"""

from __future__ import annotations

import copy
import csv
import io
import re
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from xenosite.xmet.validate import Finding, Report, core, sources, validate_ontology

RELATION_KEYS = (
    "related_to", "antonyms", "always_with", "suggests", "is_part_of", "has_part",
    "operationalizes", "predicts", "recognizes", "enumerates",
)
# Key order for concepts written by a patch (matches xmet.yaml).
KEY_ORDER = ("id", "preferred_label", "synonyms", "definition", "parents", *RELATION_KEYS)
OPS: dict[str, tuple[set[str], set[str]]] = {  # op → (required fields, optional fields)
    "set_label": ({"concept", "value"}, {"expect"}),
    "set_definition": ({"concept", "value"}, {"expect"}),
    "add_synonym": ({"concept", "value"}, set()),
    "remove_synonym": ({"concept", "value"}, set()),
    "move": ({"concept", "to"}, {"from"}),
    "add_relation": ({"concept", "relation", "target"}, set()),
    "remove_relation": ({"concept", "relation", "target"}, set()),
    "new_concept": ({"ref", "label", "definition", "parent"}, {"synonyms"}),
    "retire": ({"concept", "replaced_by"}, {"children_to", "change_type", "note"}),
}
NEW_REF = re.compile(r"^new:[A-Za-z0-9_.-]+$")
CURIE = re.compile(r"^xmet:(\d{7})$")


class PatchError(Exception):
    """A patch that is malformed or does not apply to the current ontology."""

    def __init__(self, problems: list[str]):
        super().__init__("; ".join(problems))
        self.problems = problems


@dataclass
class Patch:
    id: str
    changes: list[dict[str, Any]]
    rationale: str = ""
    author: str = ""
    path: Path | None = None
    raw: dict[str, Any] = field(default_factory=dict)


def load_patch(path: str | Path) -> Patch:
    """Read and schema-check a patch file."""
    path = Path(path)
    data = yaml.safe_load(path.read_text()) or {}
    return parse_patch(data, path)


def parse_patch(data: dict[str, Any], path: Path | None = None) -> Patch:
    problems: list[str] = []
    if not isinstance(data, dict):
        raise PatchError(["patch must be a YAML mapping"])
    changes = data.get("changes")
    if not data.get("id"):
        problems.append("missing `id`")
    if not isinstance(changes, list) or not changes:
        problems.append("`changes` must be a non-empty list")
        changes = []
    for i, ch in enumerate(changes, 1):
        op = (ch or {}).get("op")
        if op not in OPS:
            problems.append(f"change {i}: unknown op {op!r} (allowed: {', '.join(OPS)})")
            continue
        required, optional = OPS[op]
        missing = required - set(ch)
        extra = set(ch) - required - optional - {"op"}
        if missing:
            problems.append(f"change {i} ({op}): missing {', '.join(sorted(missing))}")
        if extra:
            problems.append(f"change {i} ({op}): unexpected {', '.join(sorted(extra))}")
        if op in ("add_relation", "remove_relation") and ch.get("relation") not in RELATION_KEYS:
            problems.append(f"change {i} ({op}): relation must be one of {', '.join(RELATION_KEYS)}")
        if op == "new_concept" and not NEW_REF.match(str(ch.get("ref", ""))):
            problems.append(f"change {i} (new_concept): ref must look like new:<name>")
    if problems:
        raise PatchError(problems)
    return Patch(
        id=str(data["id"]),
        changes=changes,
        rationale=str(data.get("rationale") or ""),
        author=str(data.get("author") or ""),
        path=path,
        raw=data,
    )


# --- Applying -------------------------------------------------------------------


@dataclass
class Workspace:
    """An in-memory copy of the ontology that patches are applied to."""

    text: str
    concepts: list[dict[str, Any]]
    remap_rows: list[dict[str, str]] = field(default_factory=list)
    ids: dict[str, str] = field(default_factory=dict)  # new:ref → xmet:id
    changed: set[str] = field(default_factory=set)
    added: list[str] = field(default_factory=list)
    retired: dict[str, str] = field(default_factory=dict)  # old → replacement
    next_id: int = 0

    @classmethod
    def load(cls, ontology_yaml: Path | None = None, remap: Path | None = None) -> Workspace:
        text = (ontology_yaml or core.YAML_PATH).read_text()
        ws = cls(text=text, concepts=yaml.safe_load(text)["concepts"])
        ws.next_id = _next_id(ws.concepts, remap or core.REMAP_PATH)
        return ws

    def index(self) -> dict[str, dict[str, Any]]:
        return {c["id"]: c for c in self.concepts}


def _next_id(concepts: list[dict[str, Any]], remap: Path) -> int:
    """Next number in the live id block, skipping any number ever used (live, remapped, renumbered)."""
    live = [int(m.group(1)) for c in concepts if (m := CURIE.match(c["id"]))]
    used = set(live)
    for path in (remap, remap.parent / "xmet-id-renumber.tsv"):
        if path.exists():
            used |= {int(n) for n in re.findall(r"xmet:(\d{7})", path.read_text())}
    n = max(live) + 1
    while n in used:
        n += 1
    return n


def apply_patches(ws: Workspace, patches: list[Patch]) -> None:
    """Apply patches in order. Each is all-or-nothing: on error the workspace is unchanged."""
    for patch in patches:
        snapshot = copy.deepcopy(ws)
        try:
            _apply(ws, patch)
        except PatchError as e:
            ws.__dict__.update(snapshot.__dict__)
            raise PatchError([f"{patch.id}: {p}" for p in e.problems]) from None


def _apply(ws: Workspace, patch: Patch) -> None:
    problems: list[str] = []
    # Mint ids for every new concept first so later changes can refer to them.
    for ch in patch.changes:
        if ch["op"] == "new_concept":
            if ch["ref"] in ws.ids:
                problems.append(f"{ch['ref']} defined twice")
            ws.ids[ch["ref"]] = f"xmet:{ws.next_id:07d}"
            ws.next_id += 1

    def resolve(ref: str) -> str:
        return ws.ids.get(ref, ref)

    for i, ch in enumerate(patch.changes, 1):
        idx = ws.index()
        op = ch["op"]
        where = f"change {i} ({op})"
        cid = resolve(str(ch.get("concept", "")))
        c = idx.get(cid)
        if op != "new_concept" and c is None:
            problems.append(f"{where}: {cid} is not a live concept")
            continue
        if op == "set_label":
            if "expect" in ch and c["preferred_label"] != ch["expect"]:
                problems.append(f"{where}: {cid} label is {c['preferred_label']!r}, expected {ch['expect']!r}")
                continue
            c["preferred_label"] = ch["value"]
        elif op == "set_definition":
            if "expect" in ch and _norm(c.get("definition", "")) != _norm(ch["expect"]):
                problems.append(f"{where}: {cid} definition changed since the patch was written")
                continue
            c["definition"] = ch["value"]
        elif op == "add_synonym":
            syns = c.setdefault("synonyms", [])
            if ch["value"] in syns:
                problems.append(f"{where}: {cid} already has synonym {ch['value']!r}")
                continue
            syns.append(ch["value"])
        elif op == "remove_synonym":
            syns = c.get("synonyms") or []
            if ch["value"] not in syns:
                problems.append(f"{where}: {cid} has no synonym {ch['value']!r}")
                continue
            syns.remove(ch["value"])
            if not syns:
                c.pop("synonyms", None)
        elif op == "move":
            to = resolve(ch["to"])
            if to not in idx:
                problems.append(f"{where}: new parent {to} is not a live concept")
                continue
            if "from" in ch and (c.get("parents") or [None])[0] != resolve(ch["from"]):
                problems.append(f"{where}: {cid} parent is {(c.get('parents') or [None])[0]}, expected {ch['from']}")
                continue
            c["parents"] = [to]
        elif op in ("add_relation", "remove_relation"):
            target = resolve(ch["target"])
            rel = ch["relation"]
            values = c.setdefault(rel, [])
            if op == "add_relation":
                if target not in idx:
                    problems.append(f"{where}: target {target} is not a live concept")
                elif target in values:
                    problems.append(f"{where}: {cid} already {rel} {target}")
                else:
                    values.append(target)
            else:
                if target not in values:
                    problems.append(f"{where}: {cid} has no {rel} {target}")
                else:
                    values.remove(target)
            if not values:
                c.pop(rel, None)
        elif op == "new_concept":
            new_id = ws.ids[ch["ref"]]
            parent = resolve(ch["parent"])
            if parent not in idx:
                problems.append(f"{where}: parent {parent} is not a live concept")
                continue
            concept: dict[str, Any] = {"id": new_id, "preferred_label": ch["label"]}
            if ch.get("synonyms"):
                concept["synonyms"] = list(ch["synonyms"])
            concept["definition"] = ch["definition"]
            concept["parents"] = [parent]
            ws.concepts.append(concept)
            ws.added.append(new_id)
        elif op == "retire":
            replacement = resolve(ch["replaced_by"])
            if replacement not in idx or replacement == cid:
                problems.append(f"{where}: replacement {replacement} is not another live concept")
                continue
            children_to = resolve(ch.get("children_to") or ch["replaced_by"])
            for other in ws.concepts:
                if other is c:
                    continue
                if cid in (other.get("parents") or []):
                    other["parents"] = [children_to if p == cid else p for p in other["parents"]]
                    ws.changed.add(other["id"])
                for rel in RELATION_KEYS:
                    if cid in (other.get(rel) or []):
                        vals = [replacement if v == cid else v for v in other[rel]]
                        other[rel] = [v for k, v in enumerate(vals) if v not in vals[:k] and v != other["id"]]
                        if not other[rel]:
                            other.pop(rel)
                        ws.changed.add(other["id"])
            ws.concepts.remove(c)
            ws.retired[cid] = replacement
            ws.remap_rows.append(
                {
                    "old_id": cid,
                    "new_id": replacement,
                    "change_type": ch.get("change_type") or "merged",
                    "note": ch.get("note") or f"patch {patch.id}",
                }
            )
            continue
        ws.changed.add(cid)
    if problems:
        raise PatchError(problems)


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", str(s)).strip()


# --- Writing --------------------------------------------------------------------


def _dump_concept(c: dict[str, Any]) -> str:
    from ruamel.yaml import YAML

    y = YAML()
    y.width = 100
    y.indent(mapping=2, sequence=2, offset=0)
    ordered = {k: c[k] for k in KEY_ORDER if k in c} | {k: v for k, v in c.items() if k not in KEY_ORDER}
    buf = io.StringIO()
    y.dump([ordered], buf)
    return "\n".join(line.rstrip() for line in buf.getvalue().splitlines()) + "\n"


_FIELD = re.compile(r"(?m)^(?:- |  )(?=[A-Za-z_]+:)")


def _fields(block: str) -> dict[str, str]:
    """Split one concept's YAML text into its top-level fields, keyed by name."""
    starts = [m.start() for m in _FIELD.finditer(block)] + [len(block)]
    out: dict[str, str] = {}
    for a, b in zip(starts, starts[1:]):
        seg = block[a:b]
        key = seg[2:].split(":", 1)[0]
        out[key] = seg
    return out


def _splice(original: str, old: dict[str, Any], new: dict[str, Any]) -> str:
    """Re-emit a changed concept, keeping the original text of every unchanged field."""
    fresh, orig = _fields(_dump_concept(new)), _fields(original)
    parts = []
    for key, seg in fresh.items():
        keep = key in orig and old.get(key) == new.get(key)
        parts.append(orig[key] if keep else seg)
    text = "".join(parts)
    if not text.startswith("- "):
        text = "- " + text[2:]
    return text


def render(ws: Workspace) -> str:
    """The ontology YAML with only the changed, added, and retired concepts rewritten."""
    m = re.search(r"^- id: ", ws.text, re.M)
    assert m, "no concepts in ontology YAML"
    head, body = ws.text[: m.start()], ws.text[m.start() :]
    blocks = re.split(r"(?m)^(?=- id: )", body)
    original = {re.match(r"- id: ['\"]?([^'\"\s]+)", b).group(1): b for b in blocks if b}  # type: ignore[union-attr]
    parsed = {c["id"]: c for c in yaml.safe_load(ws.text)["concepts"]}
    out = [head]
    for c in ws.concepts:
        cid = c["id"]
        if cid in original and cid not in ws.changed:
            block = original[cid]
        elif cid in original:
            block = _splice(original[cid], parsed[cid], c)
        else:
            block = _dump_concept(c)
        out.append(block if block.endswith("\n") else block + "\n")
    return "".join(out)


def write(ws: Workspace, ontology_yaml: Path | None = None, remap: Path | None = None) -> None:
    """Write the patched ontology and record retirements in the remap table.

    Existing remap rows that pointed at a now-retired concept are forwarded to its
    replacement, so every old id still resolves to a live one.
    """
    (ontology_yaml or core.YAML_PATH).write_text(render(ws))
    if not ws.remap_rows:
        return
    path = remap or core.REMAP_PATH
    fields = ["old_id", "new_id", "change_type", "note"]
    rows: list[dict[str, str]] = []
    if path.exists():
        with path.open(newline="") as fh:
            reader = csv.DictReader(fh, delimiter="\t")
            fields = list(reader.fieldnames or fields)
            rows = list(reader)
    for row in rows:
        while row.get("new_id") in ws.retired:
            row["new_id"] = ws.retired[row["new_id"]]
    rows += ws.remap_rows
    with path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, delimiter="\t", extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


# --- Review ---------------------------------------------------------------------


@dataclass
class Comparison:
    """Spec findings before and after a set of patches."""

    before: Report
    after: Report

    @staticmethod
    def _keys(fs: list[Finding]) -> dict[tuple[str, str, str], Finding]:
        return {f.key(): f for f in fs}

    @property
    def fixed(self) -> list[Finding]:
        after = self._keys(self.after.failures)
        return [f for k, f in self._keys(self.before.failures).items() if k not in after]

    @property
    def introduced(self) -> list[Finding]:
        before = self._keys(self.before.failures)
        return [f for k, f in self._keys(self.after.failures).items() if k not in before]

    @property
    def unchanged(self) -> int:
        return len(set(self._keys(self.before.failures)) & set(self._keys(self.after.failures)))


@dataclass
class Review:
    """Everything a reviewer needs: what changes, and how validation moves."""

    patches: list[Patch]
    workspace: Workspace | None
    errors: list[str]
    comparison: Comparison | None
    changes: list[str]

    @property
    def ok(self) -> bool:
        return not self.errors and self.comparison is not None and not self.comparison.introduced


def describe(before: dict[str, dict[str, Any]], ws: Workspace) -> list[str]:
    """Human-readable list of what the patches change, concept by concept."""
    after = ws.index()
    label = lambda cid: (after.get(cid) or before.get(cid) or {}).get("preferred_label", cid)  # noqa: E731
    lines: list[str] = []
    for cid in ws.added:
        c = after[cid]
        lines.append(f"**new** {cid} “{c['preferred_label']}” under {label(c['parents'][0])} ({c['parents'][0]})")
        for s in c.get("synonyms") or []:
            lines.append(f"{cid}: synonym “{s}”")
        for rel in RELATION_KEYS:
            for t in c.get(rel) or []:
                lines.append(f"{cid}: {rel} {label(t)} ({t})")
    for old, new in ws.retired.items():
        lines.append(f"**retired** {old} “{before[old]['preferred_label']}” → {new} “{label(new)}”")
    for cid in sorted(ws.changed - set(ws.added)):
        if cid not in after or cid not in before:
            continue
        a, b = before[cid], after[cid]
        name = f"{cid} “{b['preferred_label']}”"
        if a.get("preferred_label") != b.get("preferred_label"):
            lines.append(f"{cid}: label “{a['preferred_label']}” → “{b['preferred_label']}”")
        if _norm(a.get("definition", "")) != _norm(b.get("definition", "")):
            lines.append(f"{name}: definition\n  - before: {a.get('definition', '')}\n  - after: {b.get('definition', '')}")
        sa, sb = set(a.get("synonyms") or []), set(b.get("synonyms") or [])
        for s in sorted(sb - sa):
            lines.append(f"{name}: + synonym “{s}”")
        for s in sorted(sa - sb):
            lines.append(f"{name}: − synonym “{s}”")
        pa, pb = (a.get("parents") or [None])[0], (b.get("parents") or [None])[0]
        if pa != pb:
            lines.append(f"{name}: moved from {label(pa)} ({pa}) to {label(pb)} ({pb})")
        for rel in RELATION_KEYS:
            ra, rb = set(a.get(rel) or []), set(b.get(rel) or [])
            for t in sorted(rb - ra):
                lines.append(f"{name}: + {rel} {label(t)} ({t})")
            for t in sorted(ra - rb):
                lines.append(f"{name}: − {rel} {label(t)} ({t})")
    return lines


def review(patches: list[Patch]) -> Review:
    """Apply patches to a scratch copy and compare spec validation with the current ontology."""
    ws = Workspace.load()
    before_index = copy.deepcopy(ws.index())
    try:
        apply_patches(ws, patches)
    except PatchError as e:
        return Review(patches, None, e.problems, None, [])
    before = validate_ontology()
    with tempfile.TemporaryDirectory() as tmp:
        y, r = Path(tmp) / "xmet.yaml", Path(tmp) / "xmet-id-remap.tsv"
        r.write_text(core.REMAP_PATH.read_text() if core.REMAP_PATH.exists() else "old_id\tnew_id\tchange_type\tnote\n")
        write(ws, y, r)
        with sources(ontology_yaml=y, remap=r):
            after = validate_ontology()
    return Review(patches, ws, [], Comparison(before, after), describe(before_index, ws))


def format_review(rv: Review, extra: list[tuple[str, list[str], list[str], int]] | None = None) -> str:
    """Markdown report. ``extra`` adds sections as (title, fixed, introduced, unchanged)."""
    out = [f"### Patch review: {', '.join(p.id for p in rv.patches)}", ""]
    for p in rv.patches:
        if p.rationale:
            out.append(f"> {p.rationale.strip()}" + (f" — {p.author}" if p.author else ""))
    if rv.errors:
        out += ["", "**❌ Does not apply to the current ontology:**", *[f"- {e}" for e in rv.errors]]
        return "\n".join(out)
    if rv.workspace and rv.workspace.ids:
        out += ["", "New ids: " + ", ".join(f"`{k}` → `{v}`" for k, v in rv.workspace.ids.items())]
    out += ["", "#### Changes", *[f"- {line}" for line in rv.changes or ["(no effective change)"]]]
    assert rv.comparison
    sections = [
        ("Spec validation", [str(f) for f in rv.comparison.fixed], [str(f) for f in rv.comparison.introduced], rv.comparison.unchanged)
    ] + (extra or [])
    for title, fixed, introduced, unchanged in sections:
        blocking = title == "Spec validation" or any(x.startswith("[error]") for x in introduced)
        verdict = ("❌" if blocking else "⚠️") if introduced else "✅"
        out += ["", f"#### {verdict} {title}: {len(fixed)} fixed · {len(introduced)} new · {unchanged} unchanged"]
        if introduced:
            out += ["", "**New:**", *[f"- {x}" for x in introduced]]
        if fixed:
            out += ["", "**Fixed:**", *[f"- {x}" for x in fixed]]
    return "\n".join(out)
