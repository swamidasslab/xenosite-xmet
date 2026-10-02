---
title: Quality
nav_order: 3
summary: Automated review notes that show where the vocabulary most needs curation.
---

Every build runs a set of automated checks over the vocabulary. They do not decide whether a concept is right — they point a curator at places worth a second look. **{{stats.flagged}}** of {{stats.concepts}} concepts currently have at least one note.

- **Error** — breaks a rule the vocabulary relies on; fix before release.
- **Warning** — likely needs attention.
- **Info** — worth reviewing; often fine as is.

Each check below explains what it looks for and how to resolve it. Filter the table by severity, check, or branch.
