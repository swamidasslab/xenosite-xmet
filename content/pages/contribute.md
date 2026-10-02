---
title: Contribute
nav_order: 5
summary: How to suggest, correct, or extend XMET concepts.
---

XMET improves through review by the chemists who use it. There are three ways to help.

## Report a problem

Every concept page has an **Open an issue** link that starts a GitHub issue pre-filled with the concept's identifier. Use it for a wrong definition, a missing synonym, a misplaced concept, or a missing concept.

## Edit a definition or synonym

Labels, definitions, synonyms, and links live in a single authoring file, [`data/ontology/xmet.yaml`](https://github.com/swamidasslab/xenosite-xmet/blob/main/data/ontology/xmet.yaml). The **Edit source** link on each concept page opens that file at the right line on GitHub, where you can propose a change as a pull request.

## Add notes or examples

Longer notes about a concept — usage guidance, worked examples, references — go in an optional Markdown file, one per concept, under [`data/ontology/terms/`](https://github.com/swamidasslab/xenosite-xmet/tree/main/data/ontology/terms). The **Add notes** link on a concept page creates that file for you. Its text appears on the concept page once merged.

## Rules of thumb

- Definitions describe chemistry only; they do not name software or products.
- Each concept has exactly one parent. Use relations for cross-cutting links.
- Never reuse or renumber an identifier. Retire it and record the replacement instead.
