# llmwiki-skill

Two Agent Skills for a personal Markdown wiki: read-only querying (`llmwiki-query`) and paper/reference collection plus archive validation (`llmwiki-collect`).

This public repository contains reusable instructions, templates, and helper scripts. It contains no personal wiki, papers, credentials, or private research notes. Queries use summaries, notes, or original assets as needed. Paper/reference ingestion and archive validation are `llmwiki-collect` workflows.

Migration note: the former single skill at `skills/llmwiki` has been removed. Install both skills below; `llmwiki-query` replaces the old skill for questions, `llmwiki-collect` for ingestion and validation.

## Install

Clone the repository to a location of your choice:

```sh
git clone https://github.com/zedong-peng/llmwiki-skill.git
```

For pi, load them explicitly (works regardless of your current directory):

```sh
pi --skill /absolute/path/to/llmwiki-skill/skills/llmwiki-query
pi --skill /absolute/path/to/llmwiki-skill/skills/llmwiki-collect
```

Alternatively, install symlinks into the shared user skill directory used by pi and compatible agents:

```sh
mkdir -p ~/.agents/skills
ln -s /absolute/path/to/llmwiki-skill/skills/llmwiki-query ~/.agents/skills/llmwiki-query
ln -s /absolute/path/to/llmwiki-skill/skills/llmwiki-collect ~/.agents/skills/llmwiki-collect
```

Do not overwrite an existing skill installation. Restart/reload your agent after installation. For other clients, point their supported skill location at `skills/llmwiki-query` and `skills/llmwiki-collect`, retaining each `SKILL.md` and its sibling directories. Client support and discovery locations vary.

In pi:

```text
/skill:llmwiki-query What does /path/to/my-wiki say about <topic>?
/skill:llmwiki-collect Ingest https://arxiv.org/abs/<id> into /path/to/my-wiki under topic <topic>.
/skill:llmwiki-collect Ingest the blog at <url> into /path/to/my-wiki under topic <topic>.
```

Always supply the target wiki path when it is not clear from the workspace. Installing these skills does not migrate existing wiki content.

## Archive Layout

The [layout template](skills/llmwiki-collect/scaffold-template.md) describes the archive structure. Follow the target wiki's existing conventions when they differ.

## Core Rules

- Choose search and reading order to fit the task; cite the evidence used.
- Ordinary queries do not change wiki content or trigger ingestion.
- Read TeX, PDF, or official code as appropriate to the question.
- Exclude arXiv-only, unpublished papers with no code repository and no affiliation with a major company or top research lab. Missing metadata alone does not establish these conditions.
- Archive the PDF when available even if reading TeX.
- If a blog has a corresponding paper, archive the paper as primary and link the blog only when it adds unique evidence. If no paper exists, archive one PDF containing the blog's images; do not keep parallel HTML/TXT copies.
- Downloading, extracting, reading, and completing notes are different states; no note means no recorded reading. Assess reading coverage from the note's contents.
- Create formal `note.md` only after reading the paper.
- Distinguish paper-reported results, code observations, local reproduction, and interpretation.
- Update the topic index and add an entry to `wiki/log.md` after ingestion.
- Ordinary search, download, extraction, and parsing tools are allowed. Executing downloaded research code or its install/build scripts, uploading private material, and deleting, committing, or publishing wiki content require authorization.

## Package

- [Query skill entry point](skills/llmwiki-query/SKILL.md) (read-only)
- [Collect skill entry point](skills/llmwiki-collect/SKILL.md) (ingest + validate)
- [Search and retrieval](skills/llmwiki-collect/search.md)
- [Paper search tools and authentication](skills/llmwiki-collect/paper-search/README.md)
- [Layout template](skills/llmwiki-collect/scaffold-template.md)
- [Citation template](skills/llmwiki-collect/research-template/topic-template/assets/slug123_2000/citation.bib)
- [Note template](skills/llmwiki-collect/research-template/topic-template/assets/slug123_2000/note.md)

The agent uses its own download, filesystem, parser, and inspection tools.

There is no downloader, extractor, fetcher, migration script, or semantic-reading validator; downloading, safe extraction, and re-downloading ignored caches from bib URLs are agent work. Blog references use an external PDF save tool or the browser's Save as PDF action; the canonical archive is the resulting PDF.

## License

MIT. The license applies to this skill package, not papers or repositories archived using it.
