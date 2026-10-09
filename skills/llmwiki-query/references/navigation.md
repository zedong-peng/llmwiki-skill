# Navigation

Read-only address map. Write spec lives in `llmwiki-collect`.

```text
wiki/research/<topic>/
  index.md            # topic summary and catalog
  threads/            # ideas, drafts, scratch notes
  assets/<slug>_<year>/
    citation.bib      # canonical citation; entry key == directory name
    note.md           # reading record; absent = no recorded reading
```

- Slug unique wiki-wide; cross-topic = links, no duplicate archives.
- History: `wiki/log.md`, newest first.
- Reading coverage comes from the note's contents, not the presence of downloaded files.
