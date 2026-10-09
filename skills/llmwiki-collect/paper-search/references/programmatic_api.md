# Python API

For structured results, including abstracts:

```python
import sys
sys.path.insert(0, "<absolute-path-to-paper-search>/scripts")
from search_papers import search_papers

results = search_papers(
    query="<QUERY>",  # also accepts a list of queries
    start_year=2024,
    end_year=2026,
    max_results=10,
    sources=["arxiv", "semantic_scholar"],  # omitted: all six sources
)
```

Returns `{source: [paper, ...]}` before CLI deduplication and ranking. Paper fields:
`title`, `authors`, `year`, `abstract`, `url`, `venue`, `citation_count`,
`publication_date`, `source`, `doi`, `arxiv_id`; availability varies by source.
The caller can serialize this dict with `json.dump`.

Optional arguments: `parallel=False`, `start_date="YYYY-MM-DD"`,
`end_date="YYYY-MM-DD"`. Each source runs in an isolated worker; multi-query
limits apply per query per source. Source failures go to stderr and other
sources continue.

HTTP environment settings (positive values):

| Variable | Default |
| --- | --- |
| `PAPER_SEARCH_CONNECT_TIMEOUT_SECONDS` | `15` |
| `PAPER_SEARCH_TIMEOUT_SECONDS` | `300` |
| `PAPER_SEARCH_<SOURCE>_TIMEOUT_SECONDS` | inherits read timeout |
| `PAPER_SEARCH_MAX_ATTEMPTS` | `4` |

Timeouts measure connection and socket read-idle time, not total search duration.
