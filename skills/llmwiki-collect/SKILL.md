---
name: llmwiki-collect
description: Ingest academic papers and blogs into a personal Markdown wiki, or validate reference archives, when requested by the user.
---

Use the target wiki's AGENTS.md and existing conventions.

- Search as needed: [search tools](search.md).
- Exclude a paper when it is arXiv-only (unpublished), has no code repository,
  and is not from a major company or top research lab. Verify these conditions;
  missing metadata alone does not establish them.
- Archive layout and invariants: [template](scaffold-template.md).
- Archive the PDF when available, even if reading TeX.
- A blog with a corresponding paper: archive the paper; link the blog only if it
  adds evidence. Otherwise archive the blog as one PDF with images, no HTML/TXT copies.
- Write `note.md` only after reading; separate paper claims, code observations,
  local reproduction, and interpretation.
- After ingestion, update the topic index and add an entry at the top of `wiki/log.md`.
- Validation means checking the layout invariants; report, and fix only with approval.
- Do not execute downloaded research code or its install/build scripts, upload
  private material, or delete, commit, or publish wiki content without authorization.
