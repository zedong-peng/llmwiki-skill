# Layout Template

Scaffold for `research/`; create directories as needed. Adapt to an existing wiki's conventions. Example: [research-template](research-template).

```text
wiki/research/<topic>/
  index.md                        # topic catalog
  threads/
    *.md                          # ideas, drafts
  assets/
    <slug>/
      citation.bib                # key == dirname
      note.md                     # after reading only
      paper-pdf/
        <original-download-filename>.pdf
      paper-tex/
        archives/
          <original-download-filename>
        extracted/
          <archive-filename-without-extension>/
      github-repo/
        <original-repository-name>/
```

- `<slug>` is `<short-name>-<year>`, e.g. `amem-2025`; keep existing slugs.
- Each slug exists once wiki-wide; other topics link to it.
- Every reference directory is reachable from its topic index.
