"""Negation-prefix antonym detection for reaction-type labels."""
from __future__ import annotations

import re

from lib_match import normalize_label

# Stem aliases so de-/des- stripping still pairs spelling variants
STEM_ALIASES = {
    "glycosidation": "glycosylation",
    "glucosidation": "glycosylation",
    "glucuronidation": "glucuronidation",
    "sulfation": "sulfation",
    "sulphation": "sulfation",
    "sulfonation": "sulfation",
    "sulphonation": "sulfation",
    "glutathionation": "glutathionation",
    "glutathionylation": "glutathionation",
    "alkylation": "alkylation",
    "acylation": "acylation",
    "acetylation": "acetylation",
    "hydroxylation": "hydroxylation",
    "amination": "amination",
    "halogenation": "halogenation",
    "formylation": "formylation",
    "carboxylation": "carboxylation",
    "cyanidation": "cyanidation",
    "cysteination": "cysteination",
    "phosphorylation": "phosphorylation",
    "methylation": "methylation",
    "arylation": "arylation",
}

_HETERO = re.compile(r"^([onsc])-(.+)$")
_NEG = re.compile(r"^(de|des|un)(.+)$")


def split_hetero(norm: str) -> tuple[str, str]:
    m = _HETERO.match(norm)
    if m:
        return m.group(1), m.group(2)
    return "", norm


def canonical_stem(stem: str) -> str:
    stem = stem.strip("-")
    return STEM_ALIASES.get(stem, stem)


def strip_negation(core: str) -> tuple[str | None, str]:
    """Return (negation_prefix_or_None, positive_stem)."""
    m = _NEG.match(core)
    if not m:
        return None, canonical_stem(core)
    neg, rest = m.group(1), m.group(2)
    # desmethylation → demethylation-style: des + methylation if rest starts with consonant cluster
    # Prefer: desulfation = des+ulfation → treat as de+sulfation via alias table below
    special = {
        "sulfation": "sulfation",
        "ulphation": "sulfation",
        "ulfuration": "sulfuration",
        "methylation": "methylation",
        "ethylation": "ethylation",
    }
    if neg == "des" and rest in special:
        return "des", special[rest]
    if neg == "des" and rest.startswith("ulf"):
        return "des", canonical_stem("s" + rest)  # sulfation / sulfuration
    return neg, canonical_stem(rest)


def antonym_relation(a: str, b: str) -> dict[str, str] | None:
    """If a and b form a negation antonym pair, return meta; else None.

    Examples: alkylation ↔ dealkylation, O-alkylation ↔ O-dealkylation,
    glucuronidation ↔ deglucuronidation, sulfation ↔ desulfation.
    """
    na, nb = normalize_label(a), normalize_label(b)
    if not na or not nb or na == nb:
        return None
    ha, ca = split_hetero(na)
    hb, cb = split_hetero(nb)
    # hetero prefixes must agree when both present
    if ha and hb and ha != hb:
        return None
    hetero = ha or hb

    neg_a, stem_a = strip_negation(ca)
    neg_b, stem_b = strip_negation(cb)
    if stem_a != stem_b:
        return None
    if (neg_a is None) == (neg_b is None):
        return None  # both positive or both negative
    positive = stem_a
    negative_form = f"{hetero + '-' if hetero else ''}de{positive}"
    positive_form = f"{hetero + '-' if hetero else ''}{positive}"
    return {
        "stem": positive,
        "hetero": hetero,
        "positive_norm": positive_form,
        "negative_norm": negative_form,
        "source_is_negative": neg_a is not None,
        "matched_is_negative": neg_b is not None,
    }


def negation_variants(term: str) -> list[str]:
    """Generate plausible antonym surface forms for a term."""
    n = normalize_label(term)
    h, core = split_hetero(n)
    neg, stem = strip_negation(core)
    out = []
    prefix = f"{h}-" if h else ""
    if neg is None:
        # positive → try de-/des-
        out.append(f"{prefix}de{stem}")
        out.append(f"{prefix}des{stem}")
        if stem.startswith("s"):
            out.append(f"{prefix}de{stem}")  # desulfation style already
            out.append(f"{prefix}des{stem[1:]}")  # des + ulfation
    else:
        out.append(f"{prefix}{stem}")
    # unique preserve order
    seen = set()
    uniq = []
    for x in out:
        if x not in seen and x != n:
            seen.add(x)
            uniq.append(x)
    return uniq
