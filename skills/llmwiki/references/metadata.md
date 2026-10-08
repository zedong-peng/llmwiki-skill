# Metadata Contract

Use structured YAML parsing when updating metadata. Preserve existing unrelated fields. All asset paths are relative to the reference directory; never store machine-specific absolute paths in portable templates.

```yaml
schema_version: 1
paper:
  title: null
  slug: null
  topic: misc
  arxiv_id: null
  doi: null
  selected_version: null
# Non-paper references use `reference:` instead of `paper:`. A blog-only entry
# normally has `type: blog`, `url`, and `archive_format: pdf`.
# reference:
#   title: null
#   slug: null
#   topic: misc
#   type: blog
#   url: null
#   archive_format: pdf
assets: []
repositories: []
reading:
  status: not_started
  source: null
  paths: []
  scope: []
  fallback_reason: null
  note: null
ingest:
  status: queued
  updated_at: null
  exceptions: []
```

For each asset, record:

```yaml
kind: tex_source  # pdf | tex_source | supplementary
url: null  # downloadable asset URL; null for a locally rendered blog PDF
source_url: null  # canonical page URL for generated/non-downloadable captures
resolved_url: null
version: null
path: null
original_filename: null
filename_provenance: null  # content_disposition | url | derived
format: null
generated: false
archive_method: null  # website2pdf | manual_print for a rendered blog PDF
retrieved_at: null
bytes: null
sha256: null
status: pending  # pending | downloaded | failed | unavailable
error: null
extraction:
  status: not_applicable  # not_applicable | pending | extracted | failed
  path: null
  error: null
```

A migrated record may carry a top-level `legacy:` block holding the pre-migration fields unchanged. Leave it in place; do not read it as current state.

For each repository, record URL, relative path, commit, branch, retrieval date, submodule status, inspection scope, and status (`pending`, `cached`, `inspected`, `unavailable`, or `failed`). Record execution/reproduction separately, defaulting to `not_run`.

Reading status is `not_started`, `partial`, or `read`. Reading source is `tex`, `pdf`, or `blog_pdf`; repository inspection is supplemental evidence. Record which exact asset/version was read.

Overall ingest status is a summary, not a mandatory linear pipeline:

- `queued`: identified, no validated assets yet.
- `downloaded`: at least one asset cached; not yet read.
- `extracted`: source extracted; not yet read.
- `read`: reference read, note/integration still incomplete.
- `processed`: substantive note and required metadata/navigation/log checks complete.

PDF-only papers and rendered blog PDFs can go directly from `downloaded` to `read`. Optional repository failures do not invalidate completed reading. Never infer `read` or `processed` solely from download/render success or an existing note file.
