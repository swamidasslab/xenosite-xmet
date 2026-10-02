# Per-concept notes

Optional Markdown files, one per concept, named by the concept's identifier
number: `4000009.md` for `xmet:4000009`.

- **Frontmatter** holds structured fields (examples, references, …). Fields
  declared under `vocabulary.extra_fields` in `site.config.yaml` are rendered on
  the concept page by their display type; others appear under "Other fields".
- **Body** is free Markdown shown as the concept's notes. Write `[[4000009]]` to
  link another concept by its current label.

Core fields — label, definition, synonyms, parent, relations — stay in
`../xmet.yaml`; notes add to a concept but never override it.

Start from [`content/term-template.md`](../../../content/term-template.md), or use
the **Add notes** link on a concept page.
