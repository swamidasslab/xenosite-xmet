---
title: Contribute
nav_order: 5
summary: How to suggest, correct, or extend XMET concepts.
---

XMET improves through review by the chemists who use it. There are three ways to help.

## Suggest an edit

Every concept page has a **Suggest an edit** form. Change the label, definition, synonyms, parent, or relations; add a narrower concept; or propose retiring the concept in favour of another. The form turns your changes into a small patch file and opens it on GitHub, which creates a pull request for you (a free GitHub account is needed).

Within a minute, an automated review comments on the pull request. It lists exactly what would change and compares the vocabulary's automated checks before and after: which problems your edit **fixes** and which it **introduces**. You can update the suggestion until the review is clean. A maintainer then applies it or explains why not.

Several related changes — for example retiring a concept, adding its replacement, and moving its narrower concepts — belong in one suggestion, so they are reviewed together. See the [patch format](https://github.com/swamidasslab/xenosite-xmet/tree/main/data/patches) to write one by hand.

## Add notes or examples

Longer notes about a concept — usage guidance, worked examples, references — go in an optional Markdown file, one per concept, under [`data/ontology/terms/`](https://github.com/swamidasslab/xenosite-xmet/tree/main/data/ontology/terms). The **Add notes** link on a concept page creates that file for you.

## Anything else

For questions or feedback that don't fit a structured edit, use the free-form comment link at the bottom of the suggestion form.

## Rules of thumb

- Definitions describe chemistry only; they do not name software or products.
- Each concept has exactly one parent. Use relations for cross-cutting links.
- Never reuse or renumber an identifier. Retire it and record the replacement instead.
