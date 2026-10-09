# Navigation

Read-only address map. Write spec lives in `llmwiki-collect`.

```text
wiki/research/<topic>/
  index.md            # topic summary and catalog
  threads/            # ideas, drafts, scratch notes
  assets/<slug>/
    citation.bib      # canonical citation; entry key == directory name
    note.md           # reading record; absent = no recorded reading
```

- Each reference is archived once; other topics link to it.
- History: `wiki/log.md`, newest first.
- Bib `code`: repository URL, `none` = verified absent, omitted = unchecked.
- Reading coverage comes from the note's contents, not the presence of downloaded files.
