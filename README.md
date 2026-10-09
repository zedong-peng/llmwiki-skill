# llmwiki-skill

Two Agent Skills for a personal Markdown wiki: read-only querying (`llmwiki-query`) and paper/reference collection plus archive validation (`llmwiki-collect`).

This repository contains instructions, templates, and search scripts only; no wiki content, papers, or credentials.

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

## Package

- [Query skill entry point](skills/llmwiki-query/SKILL.md) (read-only)
- [Collect skill entry point](skills/llmwiki-collect/SKILL.md) (ingest + validate)
- [Search and retrieval](skills/llmwiki-collect/search.md)
- [Paper search tools and authentication](skills/llmwiki-collect/paper-search/README.md)
- [Layout template and invariants](skills/llmwiki-collect/scaffold-template.md)
- [Citation template](skills/llmwiki-collect/research-template/topic-template/assets/example-2000/citation.bib)
- [Note template](skills/llmwiki-collect/research-template/topic-template/assets/example-2000/note.md)

Downloading and extraction use the agent's own tools. Search tools need `pip install -r skills/llmwiki-collect/paper-search/requirements.txt`.

## License

MIT. The license applies to this skill package, not papers or repositories archived using it.
