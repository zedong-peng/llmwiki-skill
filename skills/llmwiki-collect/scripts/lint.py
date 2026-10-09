#!/usr/bin/env python3
"""Read-only check of the layout invariants in scaffold-template.md.

Errors: citation.bib missing or not one entry keyed by the directory name, a slug
in several topics, a reference unreachable from its topic index, broken links.
Warnings: slugs not in <short-name>-<year> form, a `code` URL with an empty
github-repo/. References without a `code` field (unchecked) are counted.
Exit status 1 on errors.

Usage: lint.py <wiki-repo-or-wiki-dir>
"""
import collections
import os
import re
import sys
from pathlib import Path

CACHE_DIRS = {"paper-pdf", "paper-tex", "github-repo", ".git"}
WIKILINK = re.compile(r"\[\[([^\]|#]+)")
MDLINK = re.compile(r"\]\(([^)\s]+)\)")
BIB_ENTRY = re.compile(r"^\s*@(\w+)\s*\{\s*([^,\s]+)\s*,", re.M)
CODE = re.compile(r"^\s*code\s*=\s*[{\"]\s*([^}\"]*?)\s*[}\"]", re.M | re.I)
SLUG = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*-\d{4}$")


def pages_under(root):
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in CACHE_DIRS)
        for f in sorted(files):
            if f.endswith(".md"):
                yield Path(dirpath, f)


def links(page, wiki, stems):
    text = page.read_text(errors="replace")
    text = re.sub(r"```.*?```|`[^`\n]*`", "", text, flags=re.S)
    for raw in WIKILINK.findall(text):
        t = raw.strip().rstrip("\\").rstrip("/")  # [[x\|alias]] in tables
        hits = [b / t for b in (page.parent, wiki)]
        hits = [h for c in hits for h in (c, c.with_name(c.name + ".md")) if h.exists()]
        if not hits and "/" not in t and t in stems:
            hits = [stems[t]]
        yield f"[[{raw.strip()}]]", hits[0].resolve() if hits else None
    for raw in MDLINK.findall(text):
        if re.match(r"[a-z][a-z0-9+.-]*:|#", raw, re.I):
            continue
        p = page.parent / raw.split("#")[0].strip("<>")
        yield f"({raw})", p.resolve() if p.exists() else None


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__.strip().splitlines()[-1])
    wiki = Path(sys.argv[1]).resolve()
    if (wiki / "wiki").is_dir():
        wiki = wiki / "wiki"
    research = wiki / "research"
    if not research.is_dir():
        sys.exit(f"no research/ under {wiki}")

    errors, warnings = [], []
    pages = list(pages_under(wiki))
    stems = {}
    for p in pages:
        stems.setdefault(p.stem, p)
    graph = {}
    for p in pages:
        graph[p.resolve()] = out = []
        for label, target in links(p, wiki, stems):
            if target is None:
                if p.name != "log.md":  # history may name pages that no longer exist
                    errors.append(f"{p.relative_to(wiki)}: broken link {label}")
            else:
                out.append(target)

    topics = collections.defaultdict(list)
    unchecked = 0
    for assets in sorted(research.glob("*/assets")):
        topic = assets.parent
        refs = [d for d in sorted(assets.iterdir()) if d.is_dir()]
        index = (topic / "index.md").resolve()
        reached, seen, todo = set(), {index}, [index]
        while todo:
            for t in graph.get(todo.pop(), []):
                reached.add(t)
                if t not in seen and t.suffix == ".md" and topic.resolve() in t.parents:
                    seen.add(t)
                    todo.append(t)
        for ref in refs:
            rel = ref.relative_to(wiki)
            topics[ref.name].append(topic.name)
            if not SLUG.match(ref.name):
                warnings.append(f"{rel}: slug is not <short-name>-<year>")
            bib = ref / "citation.bib"
            if not bib.is_file():
                errors.append(f"{rel}: missing citation.bib")
            else:
                text = re.sub(r"(?m)^\s*%.*$", "", bib.read_text(errors="replace"))
                entries = [e for e in BIB_ENTRY.findall(text)
                           if e[0].lower() not in ("comment", "preamble", "string")]
                code = CODE.search(text)
                repo = ref / "github-repo"
                if not code:
                    unchecked += 1
                elif code[1].lower() != "none" and not (
                        repo.is_dir() and any(c.name != ".gitkeep" for c in repo.iterdir())):
                    warnings.append(f"{rel}: code repository not downloaded")
                if len(entries) != 1:
                    errors.append(f"{rel}: citation.bib has {len(entries)} entries, expected 1")
                elif entries[0][1] != ref.name:
                    errors.append(f"{rel}: bib key {entries[0][1]!r} != directory name")
            r = ref.resolve()
            if not any(t == r or r in t.parents for t in reached):
                errors.append(f"{rel}: not reachable from {topic.name}/index.md")
    for slug, ts in sorted(topics.items()):
        if len(ts) > 1:
            errors.append(f"{slug}: in several topics ({', '.join(ts)}); keep one archive and link")

    for e in errors:
        print("ERROR  ", e)
    for w in warnings:
        print("warning", w)
    print(f"{len(errors)} errors, {len(warnings)} warnings, "
          f"{sum(map(len, topics.values()))} references, {unchecked} without a code field")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
