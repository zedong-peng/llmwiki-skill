# llmwiki-skill

An Agent Skill for querying a personal Markdown wiki and archiving papers and other research references.

This public repository contains reusable instructions, templates, and helper scripts. It contains no personal wiki, papers, credentials, or private research notes. Queries start from index summaries and consult original assets for details the summaries do not cover. Paper/reference ingestion and archive validation are additional workflows.

## Install

Clone the repository to a location of your choice:

```sh
git clone https://github.com/zedong-peng/llmwiki-skill.git
```

For pi, load it explicitly (works regardless of your current directory):

```sh
pi --skill /absolute/path/to/llmwiki-skill/skills/llmwiki
```

Alternatively, install a symlink into the shared user skill directory used by pi and compatible agents:

```sh
mkdir -p ~/.agents/skills
ln -s /absolute/path/to/llmwiki-skill/skills/llmwiki ~/.agents/skills/llmwiki
```

Do not overwrite an existing skill installation. Restart/reload your agent after installation. For other clients, point their supported skill location at `skills/llmwiki`, retaining `SKILL.md` and its sibling directories. Client support and discovery locations vary.

In pi:

```text
/skill:llmwiki What does /path/to/my-wiki say about <topic>?
/skill:llmwiki Ingest https://arxiv.org/abs/<id> into /path/to/my-wiki under topic <topic>.
/skill:llmwiki Ingest the blog at <url> into /path/to/my-wiki under topic <topic>.
```

Always supply the target wiki path when it is not clear from the workspace. Installing this skill does not migrate existing wiki content.

## Archive Layout

The [protocol](skills/llmwiki/references/protocol.md#canonical-layout) is the sole directory-layout specification, including legacy-cache compatibility and migration rules.

## Core Rules

- For questions, read index summaries first; consult linked original assets for missing details and cite the evidence used.
- Ordinary queries do not change wiki content or trigger ingestion.
- Read TeX/source first; inspect the official code as implementation evidence; use PDF for paper reading when source is unavailable or unusable.
- Archive the PDF when available even if reading TeX.
- If a blog has a corresponding paper, archive the paper as primary and link the blog only when it adds unique evidence. If no paper exists, archive one PDF containing the blog's images; do not keep parallel HTML/TXT copies.
- Downloading, extracting, reading, and completing notes are different states.
- Create formal `index.md` only after reading the paper. Track incomplete work in metadata.
- Distinguish paper-reported results, code observations, local reproduction, and interpretation.
- Update the topic index and add an entry to `wiki/log.md` after ingestion.
- Never automatically execute downloaded code, delete original directories, or publish personal content.

## Package

- [Skill entry point](skills/llmwiki/SKILL.md)
- [Archive and ingestion protocol](skills/llmwiki/references/protocol.md)
- [Metadata contract](skills/llmwiki/references/metadata.md)
- [Note template](skills/llmwiki/assets/note-template.md)
- [Scripts](skills/llmwiki/scripts/)

The agent uses its own download, filesystem, parser, and inspection tools. Helper scripts need Python 3 and PyYAML:

- [`scripts/lint_wiki.py`](skills/llmwiki/scripts/lint_wiki.py) checks layout, metadata, frontmatter, hashes, duplicate slugs and wikilinks.
- [`scripts/fetch_assets.py`](skills/llmwiki/scripts/fetch_assets.py) restores ignored caches (TeX archives, official repositories at the recorded commit) from `metadata.yaml`.
- [`scripts/migrate_legacy.py`](skills/llmwiki/scripts/migrate_legacy.py) moves a legacy `papers/` tree to the canonical layout (dry run by default).

There is no general downloader for new papers, extractor, or semantic-reading validator; safe archive extraction is a requirement of the workflow, not an implemented utility. Blog references use an external PDF save tool or the browser's Save as PDF action; the canonical archive is the resulting PDF.

## License

MIT. The license applies to this skill package, not papers or repositories archived using it.
