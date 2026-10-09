# Paper Search Tools

Vendored from [Microsoft ResearchStudio](https://github.com/microsoft/ResearchStudio),
`ResearchStudio-Idea/skills/paper_search`, under its MIT [license](LICENSE). Search and authentication helpers;
choose queries, sources, filtering, and presentation to fit the task.

## Search

`<tools>` is the absolute path to this `paper-search` directory.

```sh
python <tools>/scripts/search_papers.py --query "<QUERY>" \
  --start-year <YYYY> --end-year <YYYY> --max-papers 10
```

Both years are required by the CLI. It defaults to all six sources in parallel
and 10 results per source. Available options:

- `--sources arxiv dblp open_alex openreview semantic_scholar crossref`: select sources.
- `--queries "query one|query two"`: multi-query union, instead of `--query`.
- `--start-date YYYY-MM-DD`, `--end-date YYYY-MM-DD`: additional date filters.
- `--raw`: results grouped by source, without deduplication or ranking.
- `--min-score N`: optional lexical-score filter; `--no-parallel`: serial sources.

Default stdout is deduplicated and lexically ranked, with surveys placed last;
these scores are retrieval heuristics. Source failures are printed to stderr.
For abstracts and structured records, use the [Python API](references/programmatic_api.md).
The CLI has no `--json` option.

Individual `scripts/search_papers_by_<source>.py` files also expose search CLIs
(`--help`). The separate Google Scholar connector requires `scholarly` and is
not included in the unified CLI. Dependencies: `pip install -r requirements.txt`.

## Authentication

- OpenReview logs in when `OPENREVIEW_USER` / `OPENREVIEW_PASS` are configured;
  aliases `OPENREVIEW_USERNAME` / `OPENREVIEW_PASSWORD` also work. Otherwise it
  uses anonymous access.
- API credentials: `SEMANTICSCHOLAR_API_KEY`, `OPENALEX_API_KEY`.
- The standalone Google Scholar connector supports `SCRAPER_API_KEY`.

The unified CLI loads the first `.env` found from the scripts directory up to
the repository root, then `skills/*/.env`; it never looks above the repository.
Exported variables take precedence.

## Download

Search returns paper URLs and identifiers, not downloaded files. Use the agent's
browser or download tools to retrieve PDFs or source archives from paper pages,
using an existing authenticated session where needed. There is no bundled
download CLI.
