# Reference Archive Protocol

## Canonical Layout

This section is the sole directory-layout specification for the skill. Other documents refer here rather than defining another layout. Paper-specific rules are marked below; non-paper references use the same reference directory.

```text
wiki/research/<topic>/
  index.md
  threads/
    *.md 存放想法、灵感、草稿、草图、临时记录等
  assets/ 存放参考资料相关资产 参考资料可能是paper,blog,code等
    <ref_slug>/
      index.md
      metadata.yaml
      paper-pdf/
        <original-download-filename>.pdf
      paper-tex/
        archives/
          <original-download-filename>
        extracted/
          <extraction-id>/
            <original archive directory structure and filenames>
      github-repo/
        <original-repository-name>/
      supplementary/
        <original-download-filename>
```

The topic `index.md` summarizes the topic and links to its records and references. Each reference's `index.md` summarizes that reference and links to its original assets; for a paper, it is the formal paper note, not a placeholder. `metadata.yaml` can exist before reading. Optional asset directories need not exist when no assets are available. Paper references use `paper-pdf/` and `paper-tex/`; non-paper references such as blogs and software releases use `supplementary/` for their captured source assets.

A topic directory holds only `index.md`, `threads/` and `assets/`. Do not add `papers/`, per-directory guide pages, `threads/index.md` or a second log; the topic `index.md` is the only catalog. A reference slug is unique across the whole wiki: when a paper fits two topics, keep one archive and link to it from the other topic.

The wiki operation log is the single file `wiki/log.md`, newest entry first. Preserve existing navigation conventions rather than creating parallel indexes.

Page frontmatter `status` describes the page (`seed`, `active`, `stable`, `stale`). Ingest progress is recorded only in `metadata.yaml` (`ingest.status`, `reading.status`), never in the page status. Non-paper references (blogs, software releases) use a `reference:` block in place of `paper:` with the same `title`, `slug` and `topic` fields.

When a blog has a corresponding paper, the paper is the primary archive. Keep the blog as a linked supplementary source only when it adds evidence absent from the paper. When no paper exists, archive the blog as one PDF under `supplementary/`; do not create parallel HTML, text, or screenshot archives. The PDF should preserve figures and images. Record the page URL in metadata even though the page itself is not downloaded as the PDF asset.

Git policy: everything needed to re-check a paper is tracked, namely notes, metadata, `paper-pdf/`, and the full `paper-tex/extracted/` tree including figures. Recoverable caches are ignored: `paper-tex/archives/` (restored by URL and verified by SHA-256), `github-repo/` (restored at the recorded commit), and large binary supplementary files. The PDF is the canonical source for a blog-only reference, so that PDF is tracked even though it lives under `supplementary/`. `scripts/fetch_assets.py <wiki-root>` restores ignored caches in a fresh clone (dry run by default). Record the commit whenever code is inspected so the clone is reproducible.

Legacy layouts (`<topic>/papers/<slug>/` with root PDFs, `source/{archives,extracted}`, `repo/`) are usable caches and need not be redownloaded. Migrate them only with explicit authorization, using `scripts/migrate_legacy.py` (dry run by default). The script maps the legacy tree onto the canonical one, writes schema v1 metadata with the old fields preserved verbatim under `legacy:`, rewrites inbound links, and removes only loose files that are byte-identical to a file in `source/archives/`. Run it with `--caches-only` in a second clone after pulling a migrated commit to move untracked leftovers such as repository caches.

An extraction ID is an outer isolation directory, normally the archive filename with the complete recognized suffix removed (for example `.tar.gz`, `.tar`, `.tgz`, `.zip`, or `.gz`). Preserve every internal folder name, including the archive's own top-level directory. For archives without a top-level folder, files stay directly inside the isolation directory. Never flatten source trees or rename internal TeX files.

## Filenames and Versions

Prefer a safe filename supplied by Content-Disposition, then a meaningful URL basename. Strip path components and reject unsafe names. Many arXiv endpoints provide no meaningful filename: derive one from the paper ID, version, and detected format, and record that it is derived rather than calling it original. File extensions are not proof of format.

Preserve genuine downloaded names. Never overwrite an existing different file with the same name. Place colliding versions in version-specific parent directories under `paper-pdf/` or `paper-tex/archives/`; record exact relative paths. Use distinct extraction IDs for different archives/versions. Record a selected version in metadata and ensure the note identifies the evidence version. Repository names are preserved; if two owners use the same repository name, add an owner parent directory.

## Download, Rendering, and Extraction

- Cache identity is determined by URL/identifier/version and verified content, not filename alone.
- Record source URL, resolved URL, retrieval date, size, SHA-256, and filename provenance.
- Verify that PDFs are actual PDFs and that source downloads are supported archives or TeX, not HTML error pages. Check title/identifier where possible.
- Support tar, tar.gz/tgz, zip, gzip-compressed TeX, and plain TeX. Store original bytes under `archives/`, even when they are not an archive; record the actual format.
- Inspect every archive member before extraction. Reject absolute paths, traversal paths, links escaping the extraction directory, device files, and unsafe special members. Apply file-count and expanded-size limits appropriate to the environment. Never extract untrusted content over existing files.
- Extract to a new temporary isolation directory and publish the result only after successful checks. Preserve prior successful extraction on failure.
- Record failure reasons. Partial extraction or a cached download does not count as a read source.
- For a blog-only reference, save the canonical page as a PDF that includes its figures and images. Store only that PDF under `supplementary/`; do not save parallel HTML, text, or screenshot copies. Record the save method and validate that the resulting file is a PDF. If the page cannot be saved, record the failure and keep the reference unprocessed.

## Reading and Evidence

Reading priority is TeX/source first, with the official repository as implementation evidence and PDF as the paper-reading fallback. Archive the PDF even when TeX is available. Consult PDF layout/figures when useful; source-first does not prohibit PDF use. For blog-only references, the PDF is the reading source; inspect its figures and record any omitted interactive or media content.

Follow TeX includes and read substantive methods, experiments, ablations, limitations, appendix, and references. Do not report complete reading based on file existence or keyword searches. Record partial scope when context or access limits prevent full reading.

Inspect repository README, entry points, model/data/configuration, training or evaluation, and relevant implementation modules. Pin the observed commit and record submodule availability. Retain `.git/` for local cache provenance where suitable, but never assume a parent wiki Git repository backs up nested Git repositories. A local clone must not depend on a source directory that may later be removed through Git alternates.

If paper source is unavailable or unusable, record the reason and write `TeX unavailable, used PDF fallback.` in metadata and the note. For a blog-only reference, do not use the paper fallback wording; record `reading.source: blog_pdf` and the rendering boundary. Code availability does not establish experimental reproduction. Paper benchmarks, public artifact behavior, and locally measured results are separate evidence classes.

## Completion

`processed` means the reference was read, a substantive note was completed, metadata matches the evidence, and navigation/log updates and path checks were completed. Missing optional code or PDF assets may be documented exceptions; unread source content is not.

A validation pass checks file existence, hashes, relative paths, links, identifier/version consistency, repository commit and status bookkeeping. `scripts/lint_wiki.py <wiki-root>` performs the mechanical part: layout, metadata contract, frontmatter, duplicate slugs, hashes and wikilinks. It cannot certify semantic reading or scientific correctness.

Migration is a separate explicitly authorized task: dry run, review conflicts, test on a copy, apply, run the lint, and log. Never silently bulk-migrate legacy archives.
