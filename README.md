# llmwiki-skill

An Agent Skill for source-first academic paper ingestion into a personal Markdown wiki.

This public repository contains only reusable instructions and a note template. It contains no personal wiki, papers, credentials, or private research notes. The initial scope is paper ingestion and archive validation, not general life-record management.

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
/skill:llmwiki Ingest https://arxiv.org/abs/<id> into /path/to/my-wiki under topic <topic>.
```

Always supply the target wiki path when it is not clear from the workspace. Installing this skill does not migrate existing wiki content.

## Archive Layout

```text
wiki/research/<topic>/papers/<paper_slug>/
  index.md
  metadata.yaml
  paper-pdf/
    <original-paper-filename>.pdf
  paper-tex/
    archives/
      <original-source-filename>
    extracted/
      <extraction-id>/
        <original internal folders and files>
  repo/
    <original-repository-name>/
  supplementary/                    # optional
    <original-filename>
```

The extraction ID isolates each source package; internal directories are preserved unchanged. Downloads lacking a meaningful original filename get a documented derived name. Different content is never silently overwritten. Optional directories are created only when needed.

## Core Rules

- Read TeX/source first; inspect the official code as implementation evidence; use PDF for paper reading when source is unavailable or unusable.
- Archive the PDF when available even if reading TeX.
- Downloading, extracting, reading, and completing notes are different states.
- Create formal `index.md` only after reading the paper. Track incomplete work in metadata.
- Distinguish paper-reported results, code observations, local reproduction, and interpretation.
- Update wiki navigation and append an operation log after ingestion.
- Existing root PDFs and `source/` layouts remain usable; migration requires explicit authorization.
- Never automatically execute downloaded code, delete original directories, or publish personal content.

## Package

- [Skill entry point](skills/llmwiki/SKILL.md)
- [Archive and ingestion protocol](skills/llmwiki/references/protocol.md)
- [Metadata contract](skills/llmwiki/references/metadata.md)
- [Note template](skills/llmwiki/assets/note-template.md)

This first release is instruction-only. The agent uses its available download, filesystem, parser, and inspection tools. No automated downloader, extractor, or semantic-reading validator is included. Safe archive extraction is a requirement of the workflow, not an implemented utility in this package.

## License

MIT. The license applies to this skill package, not papers or repositories archived using it.
