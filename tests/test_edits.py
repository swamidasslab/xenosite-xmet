"""Edit patches: parsing, guards, atomicity, id minting, minimal rewrites, review."""

from __future__ import annotations

import shutil

import pytest
import yaml

from xenosite.xmet.edits import (
    PatchError,
    Workspace,
    apply_patches,
    parse_patch,
    render,
    review,
    write,
)
from xenosite.xmet.edits.cli import main
from xenosite.xmet.validate import core


def patch(*changes, id="t"):
    return parse_patch({"id": id, "changes": list(changes)})


@pytest.fixture
def repo(tmp_path):
    """Writable copies of the ontology and remap table."""
    y, r = tmp_path / "xmet.yaml", tmp_path / "xmet-id-remap.tsv"
    shutil.copy(core.YAML_PATH, y)
    shutil.copy(core.REMAP_PATH, r)
    shutil.copy(core.REMAP_PATH.parent / "xmet-id-renumber.tsv", tmp_path / "xmet-id-renumber.tsv")
    return y, r


def test_schema_errors_are_reported_together():
    with pytest.raises(PatchError) as e:
        parse_patch({"id": "x", "changes": [{"op": "nope"}, {"op": "set_label", "concept": "xmet:4000006"}]})
    assert len(e.value.problems) == 2


def test_untouched_concepts_keep_their_exact_text(repo):
    y, r = repo
    ws = Workspace.load(y, r)
    apply_patches(ws, [patch({"op": "add_synonym", "concept": "xmet:4000006", "value": "oxidative desaturation"})])
    before, after = y.read_text().splitlines(), render(ws).splitlines()
    assert len(after) == len(before) + 1
    assert [line for line in after if line not in before] == ["  - oxidative desaturation"]


def test_new_concepts_get_next_unused_id_and_refs_resolve(repo):
    y, r = repo
    ws = Workspace.load(y, r)
    expected = f"xmet:{ws.next_id:07d}"
    apply_patches(
        ws,
        [
            patch(
                {"op": "new_concept", "ref": "new:a", "label": "test concept a", "definition": "A test concept used only by the test suite.", "parent": "xmet:4000046"},
                {"op": "move", "concept": "xmet:4000317", "to": "new:a"},
            )
        ],
    )
    assert ws.ids == {"new:a": expected}
    assert ws.index()["xmet:4000317"]["parents"] == [expected]
    assert int(expected.split(":")[1]) > max(int(c["id"].split(":")[1]) for c in yaml.safe_load(y.read_text())["concepts"])


def test_guards_reject_stale_patches_atomically(repo):
    y, r = repo
    ws = Workspace.load(y, r)
    stale = patch(
        {"op": "add_synonym", "concept": "xmet:4000006", "value": "should not stick"},
        {"op": "move", "concept": "xmet:4000317", "from": "xmet:4000006", "to": "xmet:4000042"},
    )
    with pytest.raises(PatchError, match="expected xmet:4000006"):
        apply_patches(ws, [stale])
    assert "should not stick" not in (ws.index()["xmet:4000006"].get("synonyms") or [])
    assert render(ws) == y.read_text()


def test_retire_moves_children_rewrites_links_and_forwards_remap(repo):
    y, r = repo
    ws = Workspace.load(y, r)
    old, new = "xmet:4000109", "xmet:4000107"
    pointing = [row for row in r.read_text().splitlines() if row.split("\t")[1:2] == [old]]
    assert pointing, "fixture expects remap rows that point at the retired id"
    apply_patches(ws, [patch({"op": "retire", "concept": old, "replaced_by": new})])
    write(ws, y, r)
    data = yaml.safe_load(y.read_text())["concepts"]
    assert old not in {c["id"] for c in data}
    assert not any(old in (c.get(k) or []) for c in data for k in ("parents", "related_to", "antonyms"))
    rows = [line.split("\t") for line in r.read_text().splitlines()]
    assert [old, new, "merged", "patch t"] in rows
    assert not any(row[1] == old for row in rows[1:])


def test_review_compares_validation_with_current():
    rv = review([patch({"op": "add_synonym", "concept": "xmet:4000006", "value": "oxidative desaturation"})])
    assert rv.ok and rv.comparison and not rv.comparison.introduced
    assert any("oxidative desaturation" in line for line in rv.changes)


def test_review_reports_patches_that_do_not_apply():
    rv = review([patch({"op": "set_label", "concept": "xmet:4000006", "expect": "wrong", "value": "x"})])
    assert not rv.ok and "label is 'dehydrogenation'" in rv.errors[0]


def test_cli_check_exit_status(tmp_path):
    good = tmp_path / "good.yaml"
    good.write_text(yaml.safe_dump({"id": "g", "changes": [{"op": "add_synonym", "concept": "xmet:4000006", "value": "oxidative desaturation"}]}))
    bad = tmp_path / "bad.yaml"
    bad.write_text(yaml.safe_dump({"id": "b", "changes": [{"op": "retire", "concept": "xmet:9999999", "replaced_by": "xmet:4000006"}]}))
    assert main(["check", str(good)]) == 0
    assert main(["check", str(bad)]) == 1
