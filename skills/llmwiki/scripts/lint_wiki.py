#!/usr/bin/env python3
"""Structural lint for a wiki that follows references/protocol.md.

Checks layout, metadata contract, note frontmatter, hashes and wikilinks. It
cannot judge whether a paper was really read; see the protocol's Completion
section. Exit status is 1 when there are errors (warnings do not count).

Usage: lint_wiki.py <wiki-root> [--no-hash]
"""
import argparse
import collections
import hashlib
import os
import re
import sys

try:
    import yaml
except ImportError:
    sys.exit("PyYAML is required: pip install pyyaml")

PAGE_STATUS = {"seed", "active", "stable", "stale"}
INGEST = ["queued", "downloaded", "extracted", "read", "processed"]
READING = {"not_started", "partial", "read"}
SKIP_DIRS = ("paper-tex", "paper-pdf", "github-repo", "supplementary", "source", "repo", ".git", "node_modules")
LINK = re.compile(r"\[\[([^\]|#]+)")
errors, warnings = [], []


def err(path, msg):
    errors.append((path, msg))


def warn(path, msg):
    warnings.append((path, msg))


def frontmatter(path):
    text = open(path, errors="replace").read()
    m = re.match(r"---\n(.*?)\n---", text, re.S)
    if not m:
        return None, text
    try:
        data = yaml.safe_load(m.group(1))
        return (data if isinstance(data, dict) else {}), text
    except yaml.YAMLError:
        return False, text


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def check_reference(root, topic, slug, ref, hashes):
    rel = os.path.relpath(ref, root)
    meta_path = os.path.join(ref, "metadata.yaml")
    index_path = os.path.join(ref, "index.md")
    meta = None
    if os.path.exists(meta_path):
        try:
            meta = yaml.safe_load(open(meta_path))
        except yaml.YAMLError as e:
            err(rel, f"metadata.yaml is not valid YAML: {str(e).splitlines()[0]}")
    else:
        err(rel, "missing metadata.yaml")
    state = reading = None
    if isinstance(meta, dict):
        if meta.get("schema_version") != 1:
            err(rel, "metadata.yaml schema_version is not 1")
        paper = meta.get("paper") or meta.get("reference") or {}  # reference: non-paper items (blogs, releases)
        if paper.get("slug") != slug:
            err(rel, f"paper.slug {paper.get('slug')!r} does not match directory")
        if paper.get("topic") != topic:
            err(rel, f"paper.topic {paper.get('topic')!r} does not match topic directory")
        state = (meta.get("ingest") or {}).get("status")
        reading = (meta.get("reading") or {}).get("status")
        if state not in INGEST:
            err(rel, f"ingest.status {state!r} is not one of {INGEST}")
        if reading not in READING:
            err(rel, f"reading.status {reading!r} is not one of {sorted(READING)}")
        if state == "processed" and reading != "read":
            err(rel, "ingest.status is processed but reading.status is not read")
        if reading == "read" and not (meta.get("reading") or {}).get("source"):
            warn(rel, "reading.status is read but reading.source is empty")
        for a in meta.get("assets") or []:
            p = a.get("path")
            if not p:
                continue
            full = os.path.join(ref, p)
            if not os.path.exists(full):
                (warn if "archives" in p else err)(rel, f"asset path missing: {p}")
            elif hashes and a.get("sha256") and os.path.isfile(full) and sha256(full) != a["sha256"]:
                err(rel, f"sha256 mismatch: {p}")
    if os.path.exists(index_path):
        fm, _ = frontmatter(index_path)
        if fm is None:
            err(rel, "index.md has no frontmatter")
        elif fm is False:
            err(rel, "index.md frontmatter is not valid YAML")
        else:
            for k in ("title", "domain", "type", "status", "updated"):
                if k not in fm:
                    err(rel, f"index.md frontmatter lacks {k}")
            if fm.get("status") not in PAGE_STATUS:
                err(rel, f"index.md status {fm.get('status')!r} must be one of {sorted(PAGE_STATUS)} "
                         "(ingest progress belongs in metadata.yaml)")
    elif state in ("read", "processed") or reading == "read":
        err(rel, "paper is marked read/processed but index.md is missing")
    for legacy in ("source", "repo"):
        if os.path.isdir(os.path.join(ref, legacy)):
            err(rel, f"legacy {legacy}/ directory inside a canonical reference")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("--no-hash", action="store_true", help="skip SHA-256 verification")
    args = ap.parse_args()
    root = os.path.abspath(args.root)
    wiki = os.path.join(root, "wiki")
    research = os.path.join(wiki, "research")
    slugs = collections.defaultdict(list)

    for topic in sorted(os.listdir(research)) if os.path.isdir(research) else []:
        tdir = os.path.join(research, topic)
        if not os.path.isdir(tdir) or os.path.exists(os.path.join(tdir, ".git")):
            continue
        papers = os.path.join(tdir, "papers")
        if os.path.isdir(papers) and os.listdir(papers):
            err(os.path.relpath(papers, root), "legacy papers/ directory; migrate with scripts/migrate_legacy.py")
        assets = os.path.join(tdir, "assets")
        if os.path.isdir(assets):
            for slug in sorted(os.listdir(assets)):
                ref = os.path.join(assets, slug)
                if os.path.isdir(ref):
                    slugs[slug].append(topic)
                    check_reference(root, topic, slug, ref, not args.no_hash)
                else:
                    err(os.path.relpath(ref, root), "loose file in assets/")
    for slug, topics in slugs.items():
        if len(topics) > 1:
            err(f"assets/{slug}", f"same slug in several topics: {', '.join(topics)}; keep one archive and link")

    pages = {}
    for dp, ds, fs in os.walk(wiki):
        ds[:] = [d for d in ds if d not in SKIP_DIRS and not os.path.exists(os.path.join(dp, d, ".git"))]
        for f in fs:
            if f.endswith(".md"):
                pages[os.path.relpath(os.path.join(dp, f), wiki)[:-3]] = os.path.join(dp, f)
    basenames = {os.path.basename(p) for p in pages}
    for rel, path in sorted(pages.items()):
        if rel == "log":
            continue  # append-only history may mention pages that no longer exist
        text = re.sub(r"```.*?```", "", open(path, errors="replace").read(), flags=re.S)
        for target in LINK.findall(text):
            t = target.strip().rstrip("\\").rstrip("/")
            t = t[:-3] if t.endswith(".md") else t
            cands = {os.path.normpath(os.path.join(os.path.dirname(rel), t)), os.path.normpath(t)}
            if cands & set(pages) or ("/" not in t and t in basenames) or os.path.exists(os.path.join(wiki, t)):
                continue
            warn(rel + ".md", f"broken wikilink [[{target.strip()}]]")

    for path, msg in errors:
        print(f"ERROR   {path}: {msg}")
    for path, msg in warnings:
        print(f"warning {path}: {msg}")
    print(f"{len(errors)} errors, {len(warnings)} warnings, {sum(len(v) for v in slugs.values())} references")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
