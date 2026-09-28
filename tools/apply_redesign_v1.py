#!/usr/bin/env python3
"""Apply XMET redesign v1 (spines 1–3 + relation vocab + remap scaffolding).

Mutates data/ontology/xmet.yaml in place (caller should copy to artifacts/ first).
Writes data/mappings/xmet-id-remap.tsv for IDs minted/retired this pass.
"""

from __future__ import annotations

import csv
import copy
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
YAML_PATH = ROOT / "data/ontology/xmet.yaml"
REMAP_PATH = ROOT / "data/mappings/xmet-id-remap.tsv"

# Redesign-generation IDs (xmet:3xxxxxx)
ID_REACTION_DESCRIPTOR = "xmet:3000000"
ID_CONCEPT_RELATION = "xmet:3001000"
ID_ELIMINATION = "xmet:3000004"
ID_TRANSFER_CONJ = "xmet:3000100"
ID_ADDUCT_FORMATION = "xmet:3000200"
ID_PROTEIN_ADDUCT = "xmet:3000201"
ID_DNA_ADDUCT = "xmet:3000202"
ID_CYANIDE_CONJ = "xmet:3000203"
ID_SKELETAL_REARR = "xmet:3000300"
ID_COMPOSITE = "xmet:3000400"
ID_RING_EFFECT = "xmet:3000500"
# Reuse existing ring/aromatization concepts where present (avoid duplicate labels).
EXISTING_RING_OPENING = "xmet:0004008"
EXISTING_RING_CLOSURE = "xmet:7200006"
EXISTING_AROMATIZATION = "xmet:0000315"
EXISTING_DEAROMATIZATION = "xmet:0004001"
ID_AROM_EFFECT = "xmet:3000510"
ID_CLEAVAGE = "xmet:3000520"
ID_CLEAVAGE_RING = "xmet:3000521"
ID_CLEAVAGE_LEAVING = "xmet:3000522"
ID_CLEAVAGE_FRAG = "xmet:3000523"
ID_NL_GSH_129 = "xmet:3000600"
ID_NL_CN_27 = "xmet:3000601"
ID_REL_RELATED = "xmet:3001100"
ID_REL_SUGGESTS = "xmet:3001101"
ID_REL_ALWAYS = "xmet:3001102"
ID_REL_HAS_PART = "xmet:3001103"
ID_REL_IS_PART = "xmet:3001104"

DISPOSITION = "xmet:1000000"
REACTION_CLASS = "xmet:1100000"
PHASE_I_FAMILY = "xmet:1200000"
PHASE_II_FAMILY = "xmet:1300000"
STRUCT_DELTA = "xmet:1700000"
LEAVING_GROUP = "xmet:2200000"
OXIDATION = "xmet:0000020"
SO = "xmet:0000010"
UO = "xmet:0000011"
DH = "xmet:0000012"
HD = "xmet:0000013"
RD = "xmet:0000014"
CONJUGATION = "xmet:0000024"
REARRANGEMENT = "xmet:0002004"
TAUTOMERIZATION = "xmet:0002000"
ISOMERIZATION = "xmet:0002003"
PHASE_I = "xmet:0000001"
PHASE_II = "xmet:0000002"
PHASE_III = "xmet:0000003"
GSH = "xmet:0001030"
GLUCURONIDATION = "xmet:0001000"
SULFATION = "xmet:0001010"
ACETYLATION = "xmet:0001020"
METHYLATION = "xmet:0001040"
AA_CONJ = "xmet:0001050"
GLYCOSYLATION = "xmet:0001060"
COA = "xmet:0001061"
FORMYLATION = "xmet:0000670"
CYS_CONJ = "xmet:1300010"
NAC_CONJ = "xmet:1300011"
PHOSPHORYLATION = "xmet:1300012"
MERCAPTURIC = "xmet:0001037"


def concept(
    cid: str,
    label: str,
    definition: str,
    parents: list[str] | None = None,
    synonyms: list[str] | None = None,
    exact_match: list[str] | None = None,
    related_match: list[str] | None = None,
    close_match: list[str] | None = None,
) -> dict[str, Any]:
    c: dict[str, Any] = {
        "id": cid,
        "preferred_label": label,
        "definition": definition,
    }
    if synonyms:
        c["synonyms"] = synonyms
    if parents:
        c["parents"] = parents
    if exact_match:
        c["exact_match"] = exact_match
    if related_match:
        c["related_match"] = related_match
    if close_match:
        c["close_match"] = close_match
    return c


def parents_of(c: dict[str, Any]) -> list[str]:
    return list(c.get("parents") or [])


def set_parents(c: dict[str, Any], parents: list[str]) -> None:
    # Preserve order, unique
    seen: set[str] = set()
    out: list[str] = []
    for p in parents:
        if p not in seen:
            seen.add(p)
            out.append(p)
    c["parents"] = out


def replace_parent(c: dict[str, Any], old: str, new: str | None) -> None:
    ps = parents_of(c)
    out: list[str] = []
    for p in ps:
        if p == old:
            if new is not None and new not in out:
                out.append(new)
        elif p not in out:
            out.append(p)
    set_parents(c, out)


def remove_parents(c: dict[str, Any], forbidden: set[str]) -> None:
    set_parents(c, [p for p in parents_of(c) if p not in forbidden])


def add_parent(c: dict[str, Any], parent: str) -> None:
    ps = parents_of(c)
    if parent not in ps:
        ps.append(parent)
    set_parents(c, ps)


def spine_by_id(spines: list[dict[str, Any]], sid: str) -> dict[str, Any]:
    for s in spines:
        if s["id"] == sid:
            return s
    raise KeyError(sid)


def apply(data: dict[str, Any]) -> list[dict[str, str]]:
    remap: list[dict[str, str]] = []
    spines = data["spines"]
    concepts = data["concepts"]
    by_id: dict[str, dict[str, Any]] = {c["id"]: c for c in concepts}

    def mint(c: dict[str, Any], change_type: str, note: str, old_id: str = "") -> None:
        if c["id"] in by_id:
            raise RuntimeError(f"ID already exists: {c['id']}")
        concepts.append(c)
        by_id[c["id"]] = c
        remap.append(
            {
                "old_id": old_id,
                "new_id": c["id"],
                "change_type": change_type,
                "note": note,
            }
        )

    # --- Spine renames / merges ---
    s_disp = spine_by_id(spines, DISPOSITION)
    s_disp["preferred_label"] = "disposition stage"
    s_disp["definition"] = (
        "Conventional ADME disposition framing (Phase I / II / III and elimination). "
        "Tags for reaction classes — not chemical hierarchy parents."
    )
    s_disp["synonyms"] = ["disposition_stage", "metabolism phase", "phase"]

    s_rxn = spine_by_id(spines, REACTION_CLASS)
    s_rxn["preferred_label"] = "reaction class"
    s_rxn["definition"] = (
        "Chemist-facing chemical transformation classes for xenobiotic metabolism "
        "(Rainbow colors, conjugation, rearrangement, composites)."
    )
    s_rxn["synonyms"] = ["reaction_class", "chemical transformation", "transformation"]

    # Retire phase I/II family spines as hierarchy roots — keep spine entries as
    # legacy aliases pointing readers to reaction class / disposition.
    s_pi = spine_by_id(spines, PHASE_I_FAMILY)
    s_pi["preferred_label"] = "legacy phase I reaction family"
    s_pi["definition"] = (
        "Legacy Rainbow Phase I shelf. Prefer reaction class (with oxidation → "
        "stable/unstable oxygenation peers). Not a chemical parent for new annotation."
    )
    s_pii = spine_by_id(spines, PHASE_II_FAMILY)
    s_pii["preferred_label"] = "legacy phase II conjugation family"
    s_pii["definition"] = (
        "Legacy Phase II conjugation shelf. Prefer conjugation under reaction class "
        "with transfer vs adduct fork. Not a chemical parent for new annotation."
    )

    # Merge structural delta + leaving group into reaction descriptor spine.
    # Keep old spine ids as concepts under the new descriptor parent; rename spines.
    s_delta = spine_by_id(spines, STRUCT_DELTA)
    s_delta["preferred_label"] = "legacy structural delta"
    s_delta["definition"] = (
        "Legacy structural-delta spine; absorbed into reaction descriptor "
        f"({ID_REACTION_DESCRIPTOR})."
    )
    s_leave = spine_by_id(spines, LEAVING_GROUP)
    s_leave["preferred_label"] = "legacy leaving group spine"
    s_leave["definition"] = (
        "Legacy leaving-group spine; absorbed into reaction descriptor "
        f"({ID_REACTION_DESCRIPTOR})."
    )

    # Insert new spines after reaction class
    new_spines = [
        {
            "id": ID_REACTION_DESCRIPTOR,
            "preferred_label": "reaction descriptor",
            "definition": (
                "Orthogonal descriptors for reactions: leaving groups, ring/aromaticity "
                "effects, cleavage style, and MetID mass-shift / neutral-loss cues. "
                "Not chemical parents of reaction class."
            ),
            "synonyms": ["reaction_descriptor", "structural delta", "leaving group"],
        },
        {
            "id": ID_CONCEPT_RELATION,
            "preferred_label": "concept relation",
            "definition": (
                "Small vocabulary of associative and mereological relations used between "
                "XMET concepts (related to, suggests, always with, has part, is part of)."
            ),
            "synonyms": ["concept_relation", "relation vocabulary"],
        },
    ]
    # Place after 1100000
    insert_at = next(i for i, s in enumerate(spines) if s["id"] == REACTION_CLASS) + 1
    for ns in reversed(new_spines):
        spines.insert(insert_at, ns)

    # --- Disposition concepts ---
    by_id[DISPOSITION]["preferred_label"] = "disposition stage"
    by_id[DISPOSITION]["definition"] = s_disp["definition"]
    by_id[DISPOSITION]["synonyms"] = list(s_disp["synonyms"])

    by_id[PHASE_I]["preferred_label"] = "phase I"
    by_id[PHASE_I]["definition"] = (
        "Functionalization stage tag: oxidation, reduction, hydrolysis, and related "
        "edits that introduce or expose polar groups. Not a chemical superclass."
    )
    by_id[PHASE_II]["definition"] = (
        "Conjugation stage tag: binding to endogenous moieties. Not a chemical "
        "superclass — transfer conjugations and adducts are distinguished under "
        "reaction class."
    )
    by_id[PHASE_III]["preferred_label"] = "phase III"
    by_id[PHASE_III]["definition"] = (
        "Further handling / transport / excretion-related disposition of conjugates "
        "and metabolites. Disposition tag, not a reaction class."
    )

    if ID_ELIMINATION not in by_id:
        mint(
            concept(
                ID_ELIMINATION,
                "elimination",
                "Elimination or excretion disposition tag for xenobiotic clearance "
                "from the organism (urine, bile, breath, …).",
                parents=[DISPOSITION],
                synonyms=["elimination or excretion", "excretion"],
            ),
            "moved",
            "disposition stage: elimination/excretion tag",
        )

    # --- Reaction class backbone ---
    by_id[REACTION_CLASS]["preferred_label"] = "reaction class"
    by_id[REACTION_CLASS]["definition"] = s_rxn["definition"]
    by_id[REACTION_CLASS]["synonyms"] = list(s_rxn["synonyms"])

    # Oxidation / reduction / isoredox near top; five colors fall under those.
    # SO + UO + DH → oxidation; RD is the reduction class; HD → isoredox.
    by_id[OXIDATION]["definition"] = (
        "Oxidations and related increase of oxidation state / oxygen installation. "
        "Rainbow stable oxygenation, unstable oxygenation, and dehydrogenation sit here; "
        "peer of reduction and isoredox under reaction class."
    )
    remove_parents(by_id[OXIDATION], {PHASE_I, PHASE_I_FAMILY})
    set_parents(by_id[OXIDATION], [REACTION_CLASS])

    for color_id, parent, note in [
        (SO, OXIDATION, "stable oxygenation under oxidation"),
        (UO, OXIDATION, "unstable oxygenation under oxidation"),
        (DH, OXIDATION, "dehydrogenation under oxidation"),
    ]:
        remove_parents(by_id[color_id], {PHASE_I, PHASE_I_FAMILY, REACTION_CLASS})
        set_parents(by_id[color_id], [parent])
        remap.append(
            {
                "old_id": color_id,
                "new_id": color_id,
                "change_type": "relabeled",
                "note": note + " (kept id)",
            }
        )

    # Reduction class = Rainbow reduction color at top level
    remove_parents(by_id[RD], {PHASE_I, PHASE_I_FAMILY, OXIDATION})
    set_parents(by_id[RD], [REACTION_CLASS])
    by_id[RD]["definition"] = (
        "Reduction class (Rainbow reduction color): remove oxygen or add hydrogen(s). "
        "Peer of oxidation and isoredox under reaction class."
    )

    ID_ISOREDOX = "xmet:3000005"
    if ID_ISOREDOX not in by_id:
        mint(
            concept(
                ID_ISOREDOX,
                "isoredox",
                "Transformations that do not change net oxidation state in the Rainbow "
                "sense (e.g. hydrolysis). Peer of oxidation and reduction under reaction class.",
                parents=[REACTION_CLASS],
                synonyms=["redox-neutral transformation", "isoredox class"],
            ),
            "moved",
            "isoredox class under reaction class",
        )
    remove_parents(by_id[HD], {PHASE_I, PHASE_I_FAMILY, REACTION_CLASS, OXIDATION})
    set_parents(by_id[HD], [ID_ISOREDOX])
    by_id[HD]["definition"] = (
        "Rainbow hydrolysis color: water addition cleaves amide, ester, ether, or related "
        "bonds. Nested under isoredox (redox-neutral)."
    )

    # Reparent direct children of legacy phase I family → appropriate homes
    for c in list(concepts):
        if PHASE_I_FAMILY not in parents_of(c):
            continue
        cid = c["id"]
        if cid in (SO, UO, DH, HD, RD):
            replace_parent(c, PHASE_I_FAMILY, None)
            continue
        # Class nodes under phase I family → hang under matching color when possible
        replace_parent(c, PHASE_I_FAMILY, REACTION_CLASS)
        remove_parents(c, {PHASE_I})

    # --- Conjugation fork ---
    remove_parents(by_id[CONJUGATION], {PHASE_II, PHASE_II_FAMILY})
    set_parents(by_id[CONJUGATION], [REACTION_CLASS])
    by_id[CONJUGATION]["definition"] = (
        "Addition of an endogenous or trapping moiety. Split into transfer "
        "conjugation (clearance-oriented) and adduct formation (electrophile capture)."
    )
    by_id[CONJUGATION]["preferred_label"] = "conjugation"

    if ID_TRANSFER_CONJ not in by_id:
        mint(
            concept(
                ID_TRANSFER_CONJ,
                "transfer conjugation",
                "Metabolic transfer of an endogenous moiety (glucuronide, sulfate, "
                "acetyl, methyl, amino acid, glycosyl, CoA, …) typically supporting "
                "clearance. Distinct from reactive adduct formation.",
                parents=[CONJUGATION],
                synonyms=["metabolic transfer conjugation", "Phase II transfer conjugation"],
            ),
            "moved",
            "conjugation fork: transfer branch",
        )
    if ID_ADDUCT_FORMATION not in by_id:
        mint(
            concept(
                ID_ADDUCT_FORMATION,
                "adduct formation",
                "Electrophile capture / macromolecular or trapping adduct formation "
                "(GSH, protein, DNA, cyanide). Distinct from transfer conjugation.",
                parents=[CONJUGATION],
                synonyms=[
                    "reactive-species capture conjugation",
                    "adduct conjugation",
                ],
            ),
            "moved",
            "conjugation fork: adduct branch",
        )

    transfer_ids = {
        GLUCURONIDATION,
        SULFATION,
        ACETYLATION,
        METHYLATION,
        AA_CONJ,
        GLYCOSYLATION,
        COA,
        FORMYLATION,
        PHOSPHORYLATION,
        "xmet:0001053",  # taurine
        "xmet:0001051",  # glycine
    }
    # All direct children of phase II family that are not GSH/mercapturic/NAC/cys adduct-like
    adduct_ids = {GSH, MERCAPTURIC, CYS_CONJ, NAC_CONJ}

    for c in concepts:
        ps = parents_of(c)
        if PHASE_II_FAMILY in ps or PHASE_II in ps:
            remove_parents(c, {PHASE_II, PHASE_II_FAMILY})
            if c["id"] in adduct_ids or c["id"] == GSH:
                add_parent(c, ID_ADDUCT_FORMATION)
            elif c["id"] in transfer_ids or c["id"].startswith("xmet:13001"):
                # 13001xx class nodes — GSH-related class nodes go to adducts
                lab = c["preferred_label"].lower()
                if "gsh" in lab or "glutathion" in lab:
                    add_parent(c, ID_ADDUCT_FORMATION)
                else:
                    add_parent(c, ID_TRANSFER_CONJ)
            elif CONJUGATION in ps or c["id"] == CONJUGATION:
                pass
            else:
                # default conjugation leaves → transfer unless clearly adduct
                lab = c["preferred_label"].lower()
                if any(k in lab for k in ("gsh", "glutathion", "mercaptur", "cysteine conjug", "n-acetylcysteine")):
                    add_parent(c, ID_ADDUCT_FORMATION)
                else:
                    add_parent(c, ID_TRANSFER_CONJ)

    # GSH preferred label
    by_id[GSH]["preferred_label"] = "glutathione conjugation"
    by_id[GSH]["synonyms"] = list(
        dict.fromkeys(
            (by_id[GSH].get("synonyms") or [])
            + ["glutathionation", "GSH conjugation", "GSH adduct formation"]
        )
    )
    by_id[GSH]["definition"] = (
        "Conjugation / adduct formation with glutathione (electrophile capture). "
        "Under adduct formation, not transfer conjugation. Soft-suggests protein adduct."
    )
    set_parents(by_id[GSH], [ID_ADDUCT_FORMATION])

    if ID_PROTEIN_ADDUCT not in by_id:
        mint(
            concept(
                ID_PROTEIN_ADDUCT,
                "protein adduct formation",
                "Covalent adduct formation with protein nucleophiles. Often suggested "
                "by soft-electrophile / GSH-trapping evidence.",
                parents=[ID_ADDUCT_FORMATION],
                synonyms=["protein adduct", "protein binding adduct"],
            ),
            "moved",
            "adduct fork: protein",
        )
    if ID_DNA_ADDUCT not in by_id:
        mint(
            concept(
                ID_DNA_ADDUCT,
                "DNA adduct formation",
                "Covalent adduct formation with DNA nucleophiles. Often suggested by "
                "hard-electrophile / cyanide-trapping evidence.",
                parents=[ID_ADDUCT_FORMATION],
                synonyms=["DNA adduct"],
            ),
            "moved",
            "adduct fork: DNA",
        )
    if ID_CYANIDE_CONJ not in by_id:
        mint(
            concept(
                ID_CYANIDE_CONJ,
                "cyanide conjugation",
                "Trapping of hard electrophiles (e.g. iminium) with cyanide. Distinct "
                "from cyanide as a leaving group. Soft-suggests DNA adduct formation.",
                parents=[ID_ADDUCT_FORMATION],
                synonyms=["cyanide trapping", "cyanide adduct formation", "CN trapping"],
            ),
            "moved",
            "adduct fork: cyanide",
        )

    # Soft suggestions via related_match (relation vocab CURIEs used as tags later)
    def add_related(cid: str, target: str) -> None:
        c = by_id[cid]
        rm = list(c.get("related_match") or [])
        if target not in rm:
            rm.append(target)
        c["related_match"] = rm

    add_related(GSH, ID_PROTEIN_ADDUCT)
    add_related(ID_CYANIDE_CONJ, ID_DNA_ADDUCT)

    # --- Rearrangement shelf ---
    remove_parents(by_id[REARRANGEMENT], {PHASE_I, PHASE_I_FAMILY})
    set_parents(by_id[REARRANGEMENT], [REACTION_CLASS])
    by_id[REARRANGEMENT]["definition"] = (
        "Non–enzyme-mediated molecular rearrangement shelf (tautomerization, "
        "isomerization, skeletal rearrangement). Not a Rainbow reaction color."
    )
    set_parents(by_id[TAUTOMERIZATION], [REARRANGEMENT])
    set_parents(by_id[ISOMERIZATION], [REARRANGEMENT])
    if ID_SKELETAL_REARR not in by_id:
        mint(
            concept(
                ID_SKELETAL_REARR,
                "skeletal rearrangement",
                "Rearrangement that changes atom connectivity of the heavy-atom "
                "skeleton (sparse in xenobiotic metabolism).",
                parents=[REARRANGEMENT],
            ),
            "moved",
            "rearrangement: skeletal child",
        )

    # --- Composites ---
    if ID_COMPOSITE not in by_id:
        mint(
            concept(
                ID_COMPOSITE,
                "composite transformation",
                "Multi-step or multi-part transformation described as a unit; "
                "constituents linked via has part / is part of.",
                parents=[REACTION_CLASS],
                synonyms=["composite", "composite pathway"],
            ),
            "moved",
            "reaction class: composite shelf",
        )

    # --- Reaction descriptor spine concepts ---
    if ID_REACTION_DESCRIPTOR not in by_id:
        mint(
            concept(
                ID_REACTION_DESCRIPTOR,
                "reaction descriptor",
                "Orthogonal descriptors (leaving group, ring/aromaticity effect, "
                "cleavage, mass shift) used alongside reaction class.",
                parents=["xmet:0000000"],
                synonyms=["reaction_descriptor"],
            ),
            "moved",
            "new spine root concept",
        )

    # Reparent leaving-group and structural-delta roots under descriptor
    set_parents(by_id[LEAVING_GROUP], [ID_REACTION_DESCRIPTOR])
    by_id[LEAVING_GROUP]["preferred_label"] = "leaving group"
    by_id[LEAVING_GROUP]["definition"] = (
        "Fragment or moiety that departs in cleavage / substitution / dealkylation / "
        "hydrolysis. Pragmatic stop-word filter for metabolite annotation."
    )
    set_parents(by_id[STRUCT_DELTA], [ID_REACTION_DESCRIPTOR])
    by_id[STRUCT_DELTA]["preferred_label"] = "structural delta"
    by_id[STRUCT_DELTA]["definition"] = (
        "Structural / formula / aromaticity / bond-order change facets under "
        "reaction descriptor."
    )

    # Ensure leaving-group children still under leaving group
    for c in concepts:
        if LEAVING_GROUP in parents_of(c) and c["id"] != LEAVING_GROUP:
            continue  # already correct
        if STRUCT_DELTA in parents_of(c) and c["id"] != STRUCT_DELTA:
            continue

    if ID_RING_EFFECT not in by_id:
        mint(
            concept(
                ID_RING_EFFECT,
                "ring effect",
                "Ring opening, closure, expansion, or contraction accompanying a reaction.",
                parents=[ID_REACTION_DESCRIPTOR],
            ),
            "moved",
            "descriptor: ring effect",
        )
    # Re-home existing ring opening/closure under ring effect (descriptor shelf).
    if EXISTING_RING_OPENING in by_id:
        set_parents(by_id[EXISTING_RING_OPENING], [ID_RING_EFFECT])
        remove_parents(by_id[EXISTING_RING_OPENING], {REACTION_CLASS, "xmet:0004000"})
    if EXISTING_RING_CLOSURE in by_id:
        set_parents(by_id[EXISTING_RING_CLOSURE], [ID_RING_EFFECT])
    if ID_AROM_EFFECT not in by_id:
        mint(
            concept(
                ID_AROM_EFFECT,
                "aromaticity effect",
                "Aromatization, rearomatization, or dearomatization as a reaction descriptor.",
                parents=[ID_REACTION_DESCRIPTOR],
            ),
            "moved",
            "descriptor: aromaticity effect",
        )
    if EXISTING_AROMATIZATION in by_id:
        # Keep reaction-class home (e.g. under dehydrogenation); link descriptor softly.
        add_related(EXISTING_AROMATIZATION, ID_AROM_EFFECT)
    if EXISTING_DEAROMATIZATION in by_id:
        add_related(EXISTING_DEAROMATIZATION, ID_AROM_EFFECT)
    if ID_CLEAVAGE not in by_id:
        mint(
            concept(
                ID_CLEAVAGE,
                "cleavage",
                "Directional bond-break cue: ring-opening cleavage, cleavage with "
                "leaving group, or fragmenting cleavage (≥2 metabolite products).",
                parents=[ID_REACTION_DESCRIPTOR],
            ),
            "moved",
            "descriptor: cleavage parent",
        )
        mint(
            concept(
                ID_CLEAVAGE_RING,
                "ring-opening cleavage",
                "Bond break that opens a ring; always with ring opening.",
                parents=[ID_CLEAVAGE],
            ),
            "moved",
            "descriptor: ring-opening cleavage",
        )
        mint(
            concept(
                ID_CLEAVAGE_LEAVING,
                "cleavage with leaving group",
                "One product is the retained scaffold; the other is a small/generic "
                "leaving fragment.",
                parents=[ID_CLEAVAGE],
            ),
            "moved",
            "descriptor: cleavage with leaving group",
        )
        mint(
            concept(
                ID_CLEAVAGE_FRAG,
                "fragmenting cleavage",
                "Cleavage yields two or more xenobiotic-derived metabolites that each "
                "deserve product-level identity (not collapsed to leaving group).",
                parents=[ID_CLEAVAGE],
            ),
            "moved",
            "descriptor: fragmenting cleavage",
        )

    # Mass-shift / NL seeds under existing mass shift if present
    mass_shift = by_id.get("xmet:1700011")
    if mass_shift:
        set_parents(mass_shift, [STRUCT_DELTA])
    if ID_NL_GSH_129 not in by_id:
        mint(
            concept(
                ID_NL_GSH_129,
                "GSH pyroglutamate neutral loss",
                "Characteristic MS neutral loss of ~129 Da (pyroglutamate) suggesting "
                "glutathione conjugation / GSH adduct.",
                parents=["xmet:1700011"] if "xmet:1700011" in by_id else [STRUCT_DELTA],
                synonyms=["NL 129", "pyroglutamate neutral loss"],
            ),
            "moved",
            "MetID: GSH NL 129",
        )
        add_related(ID_NL_GSH_129, GSH)
    if ID_NL_CN_27 not in by_id:
        mint(
            concept(
                ID_NL_CN_27,
                "cyanide neutral loss",
                "Characteristic MS neutral loss / mass cue of ~27 Da (HCN) suggesting "
                "cyanide conjugation / trapping.",
                parents=["xmet:1700011"] if "xmet:1700011" in by_id else [STRUCT_DELTA],
                synonyms=["NL 27", "HCN neutral loss"],
            ),
            "moved",
            "MetID: cyanide NL 27",
        )
        add_related(ID_NL_CN_27, ID_CYANIDE_CONJ)

    # Soft links from mass shifts to conjugations
    for mid, target in [
        ("xmet:1700104", GLUCURONIDATION),
        ("xmet:1700105", SULFATION),
        ("xmet:1700106", GSH),
    ]:
        if mid in by_id:
            add_related(mid, target)

    # --- Concept relation vocabulary ---
    if ID_CONCEPT_RELATION not in by_id:
        mint(
            concept(
                ID_CONCEPT_RELATION,
                "concept relation",
                "Parent for the small relation vocabulary used across XMET spines.",
                parents=["xmet:0000000"],
            ),
            "moved",
            "relation vocabulary root",
        )
    if ID_REL_RELATED not in by_id:
        mint(
            concept(
                ID_REL_RELATED,
                "related to",
                "Associated with; no frequency or necessity claim.",
                parents=[ID_CONCEPT_RELATION],
                synonyms=["relatedTo", "xmet:relatedTo"],
                exact_match=["skos:related"],
            ),
            "moved",
            "relation: related to",
        )
        mint(
            concept(
                ID_REL_SUGGESTS,
                "suggests",
                "Often (but not always) associated with.",
                parents=[ID_CONCEPT_RELATION],
                synonyms=["suggests", "xmet:suggests"],
            ),
            "moved",
            "relation: suggests",
        )
        mint(
            concept(
                ID_REL_ALWAYS,
                "always with",
                "Whenever this term applies, the target also applies (or a term under "
                "the target if it is a category root).",
                parents=[ID_CONCEPT_RELATION],
                synonyms=["alwaysWith", "xmet:alwaysWith"],
            ),
            "moved",
            "relation: always with",
        )
        mint(
            concept(
                ID_REL_HAS_PART,
                "has part",
                "Has as a constituent / part (e.g. composite has part reaction).",
                parents=[ID_CONCEPT_RELATION],
                synonyms=["hasPart", "xmet:hasPart"],
                exact_match=["dcterms:hasPart"],
            ),
            "moved",
            "relation: has part",
        )
        mint(
            concept(
                ID_REL_IS_PART,
                "is part of",
                "Is a constituent / part of. Inverse of has part.",
                parents=[ID_CONCEPT_RELATION],
                synonyms=["isPartOf", "xmet:isPartOf"],
                exact_match=["dcterms:isPartOf"],
            ),
            "moved",
            "relation: is part of",
        )

    # Ring-opening cleavage always with ring opening
    add_related(ID_CLEAVAGE_RING, EXISTING_RING_OPENING)

    # Legacy family spines: hang under root but not used as chem parents
    set_parents(by_id[PHASE_I_FAMILY], ["xmet:0000000"])
    set_parents(by_id[PHASE_II_FAMILY], ["xmet:0000000"])

    # Record spine renames in remap
    for oid, note in [
        (DISPOSITION, "relabel metabolism phase → disposition stage"),
        (REACTION_CLASS, "relabel chemical transformation → reaction class"),
        (PHASE_I_FAMILY, "retire as chem parent; legacy label"),
        (PHASE_II_FAMILY, "retire as chem parent; legacy label"),
        (STRUCT_DELTA, "absorbed under reaction descriptor"),
        (LEAVING_GROUP, "absorbed under reaction descriptor"),
    ]:
        remap.append(
            {
                "old_id": oid,
                "new_id": oid,
                "change_type": "relabeled",
                "note": note,
            }
        )

    return remap


def dump_yaml(data: dict[str, Any], path: Path) -> None:
    # Prefer ruamel if available for readability; fall back to safe dump.
    try:
        from ruamel.yaml import YAML

        yaml_rt = YAML()
        yaml_rt.indent(mapping=2, sequence=2, offset=0)
        yaml_rt.width = 100
        yaml_rt.default_flow_style = False
        with path.open("w") as fh:
            yaml_rt.dump(data, fh)
    except Exception:
        path.write_text(
            yaml.safe_dump(
                data,
                sort_keys=False,
                allow_unicode=True,
                width=100,
                default_flow_style=False,
            )
        )


def main() -> None:
    artifacts = ROOT / "artifacts"
    artifacts.mkdir(exist_ok=True)
    backup = artifacts / "xmet.yaml.pre-redesign-v1.yaml"
    text = YAML_PATH.read_text()
    if not backup.exists():
        backup.write_text(text)
        print(f"backup → {backup}")

    data = yaml.safe_load(text)
    remap = apply(data)
    dump_yaml(data, YAML_PATH)

    REMAP_PATH.parent.mkdir(parents=True, exist_ok=True)
    with REMAP_PATH.open("w", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=["old_id", "new_id", "change_type", "note"],
            delimiter="\t",
        )
        writer.writeheader()
        for row in remap:
            writer.writerow(row)
    print(f"wrote {YAML_PATH}")
    print(f"wrote {REMAP_PATH} ({len(remap)} rows)")
    print(f"concepts: {len(data['concepts'])}")


if __name__ == "__main__":
    main()
