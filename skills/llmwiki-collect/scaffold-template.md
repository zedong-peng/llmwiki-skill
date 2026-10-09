# Layout Template

Scaffold for `research/`; create directories as needed. Adapt to an existing wiki's conventions. Example: [research-template](research-template).

```text
wiki/research/<topic>/
  index.md                        # topic catalog
  threads/
    *.md                          # ideas, drafts
  assets/
    <slug>_<year>/
      citation.bib                # key == dirname
      note.md                     # after reading only
      paper-pdf/
        <original-download-filename>.pdf
      paper-tex/
        archives/
          <original-download-filename>
        extracted/
          <extraction-id>/
      github-repo/
        <original-repository-name>/
```
